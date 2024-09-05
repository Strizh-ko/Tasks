"""
Приложение подразумевает ежедневный вход пользователя, начисление баллов за вход.
Нужно отследить момент первого входа игрока для аналитики.
Также у игрока имеются игровые бонусы в виде нескольких типов бустов.
Нужно описать модели игрока и бустов с возможностью начислять игроку бусты за прохождение уровней или вручную.
"""

from django.db import models
from django.utils import timezone


class Player(models.Model):
    username = models.CharField(max_length=64, unique=True)
    first_time_login = models.DateTimeField(null=True, blank=True)
    last_time_login = models.DateTimeField(null=True, blank=True)
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    # Смотрим, когда зашел пользователь. Ну и отсыпаем ему очков за вход. :-)
    def login(self):
        if not self.first_time_login:
            self.first_time_login = timezone.now()
        self.last_time_login = timezone.now()
        self.points += 5
        self.save()


class Boost(models.Model):

    types_of_boosts = (
        ('S', 'Strength'),
        ('P', 'Perception'),
        ('E', 'Endurance'),
        ('C', 'Charisma'),
        ('I', 'Intelligence'),
        ('A', 'Agility'),
        ('L', 'Luck')
    )

    player = models.ForeignKey(Player, related_name='boosts', on_delete=models.CASCADE)
    boost_type = models.CharField(max_length=32, choices=types_of_boosts)
    rate = models.IntegerField(default=1)
    applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.username} used {self.get_boost_type_display()} boost x{self.rate}"


# Бустим юзера
def give_boost(player, boost_type, rate=1):
    boost, active = Boost.objects.get_or_create(player=player, boost_type=boost_type)
    if not active:
        boost.rate += rate
        boost.save()
    return boost





"""
Написать два метода:
1. Присвоение игроку приза за прохождение уровня.
2. Выгрузку в csv следующих данных: id игрока, название уровня, пройден ли уровень, полученный приз за уровень. 
    Учесть, что записей может быть 100 000 и более.
"""
# Не описывать метод __str__, так же как и не прописывать "related_name" - дурной тон в программировании...
# По крайней мере, меня так учили. :-) Корректировать ваш код не буду, с вашего позволения. Т.к. с меня 2 метода.

import csv
from django.db import models
from django.utils import timezone


class Player(models.Model):
    player_id = models.CharField(max_length=100)

    def give_prize(self, level):
        player_level = PlayerLevel.objects.get(player=self, level=level)

        if player_level.is_completed and not LevelPrize.objects.filter(level=level, player=self).exists():
            level_prize = LevelPrize.objects.filter(level=level).first()

            if level_prize:
                LevelPrize.objects.create(
                    level=level,
                    prize=level_prize.prize,
                    player=self,
                    received=timezone.now()
                )

    @staticmethod
    def export_data(filename='player_data.csv'):
        header = ['Player ID', 'Level Title', 'Is Completed', 'Prize Title']

        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)

            player_levels = PlayerLevel.objects.select_related('player', 'level').iterator()
            for pl in player_levels:
                prize = LevelPrize.objects.filter(level=pl.level, player=pl.player).first()
                writer.writerow([
                    pl.player.player_id,
                    pl.level.title,
                    pl.is_completed,
                    prize.prize.title if prize else ''
                ])


class Level(models.Model):
    title = models.CharField(max_length=100)
    order = models.IntegerField(default=0)


class Prize(models.Model):
    title = models.CharField(max_length=100)


class PlayerLevel(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    completed = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0)


class LevelPrize(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    received = models.DateField()

    # Одного поля явно не хватает...
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='level_prizes', null=True)
