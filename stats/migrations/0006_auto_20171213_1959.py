# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_auto_20171212_1802'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='champion',
            name='riot_id',
        ),
        migrations.RemoveField(
            model_name='item',
            name='riot_id',
        ),
        migrations.AddField(
            model_name='match',
            name='duration',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='champ_level',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='combat_player_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='damage_dealt_to_objectives',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='damage_dealt_to_turrets',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='damage_self_mitigated',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='double_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_blood_assist',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_blood_kill',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_inhibitor_assist',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_inhibitor_kill',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_tower_assist',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='first_tower_kill',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='gold_earned',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='gold_spent',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='inhibitor_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='killing_sprees',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='largest_critical_strike',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='largest_killing_spree',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='longest_time_spent_living',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='magic_damage_dealt',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='magic_damage_dealt_to_champions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='magical_damage_taken',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='neutral_minions_killed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='neutral_minions_killed_enemy_jungle',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='neutral_minions_killed_team_jungle',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='objective_player_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='penta_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='physical_damage_dealt',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='physical_damage_dealt_to_champions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='physical_damage_taken',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='quadra_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='sight_wards_bought_in_game',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='time_ccing_others',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_damage_dealt',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_damage_dealt_to_champions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_damage_taken',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_heal',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_minions_killed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_player_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_score_rank',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='total_time_crowd_control_dealt',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='triple_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='true_damage_dealt',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='true_damage_dealt_to_champions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='true_damage_taken',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='turret_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='vision_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='vision_wards_bought_in_game',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='wards_killed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playermatch',
            name='wards_placed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='baron_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='first_blood',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='first_dragon',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='first_inhibitor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='first_rift_herald',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='first_tower',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='inhibitor_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='teammatch',
            name='tower_kills',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='teammatch',
            name='win',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='teamplayer',
            name='isLeader',
            field=models.BooleanField(default=False),
        ),
    ]
