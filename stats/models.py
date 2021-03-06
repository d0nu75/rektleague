import datetime
import time
import math
import re
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Sum, Q, Case, When, F, Value, ExpressionWrapper
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

class Season(models.Model):
    tournament_id = models.IntegerField(default=0)
    team_size = models.IntegerField(default=5)
    pick_type = models.CharField(max_length=30)
    map_type = models.CharField(max_length=30)
    spectator_type = models.CharField(max_length=30)
    splash = models.ImageField(upload_to='stats/season_splashes', default='')

    def __str__(self):
        return "Season " + str(self.pk)

    def get_weeks(self):
        return Week.objects.filter(season=self).order_by('-number')

    def get_weeks_desc(self):
        return Week.objects.filter(season=self).order_by('number')

    def get_top_banned(self):
        num_matches = Match.objects.filter(series__week__season=self).exclude(duration=0).count()
        if num_matches == 0:
            return TeamMatchBan.objects.none()
        return TeamMatchBan.objects.filter(team__season=self).values('champion__name', 'champion__icon', 'champion').annotate(ban_rate=Count('champion') * 100 / num_matches).order_by('-ban_rate')[:20]

    def get_top_picked(self):
        num_matches = Match.objects.filter(series__week__season=self).exclude(duration=0).count()
        if num_matches == 0:
            return PlayerMatch.objects.none()
        return PlayerMatch.objects.filter(match__series__week__season=self).values('champion__name', 'champion__icon', 'champion').annotate(pick_rate=Count('champion') * 100 / num_matches).order_by('-pick_rate')[:20]

    def get_champ_stats(self):
        num_matches = Match.objects.filter(series__week__season=self).exclude(duration=0).count()
        stats = PlayerMatch.objects.filter(match__series__week__season=self)
        win_ids = [o.id for o in stats if o.win()]
        return stats.filter(id__in=win_ids).values('champion__name', 'champion__icon', 'champion').annotate(pick_rate=Count('champion') * 100 / num_matches)

    def get_winner(self):
        return Team.objects.filter(season=self, season_win=True)

    def next_week(self):
        ret = Week.objects.filter(season=self, date__gte=datetime.datetime.now())
        if self.id > 2 and len(ret) > 0:
            return ret[0]
        return self.get_weeks()[0]


class Week(models.Model):
    season = models.ForeignKey(Season)
    number = models.IntegerField(default=1)
    regular = models.BooleanField(default=True)
    title = models.CharField(max_length=50, default="")
    date = models.DateTimeField(null=True, blank=True)

    def name_w_title(self):
        if self.title != "" and self.title != " ":
            return "Week " + str(self.number) + " - " + self.title
        return "Week " + str(self.number)

    def __str__(self):
        return str(self.season) + ": Week " + str(self.number)

class Role(models.Model):
    name = models.CharField(max_length=15)
    icon = models.ImageField(upload_to='stats/role/icon', default='')
    isFill = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Champion(models.Model):
    name = models.CharField(max_length=40)
    title = models.CharField(max_length=40)
    icon = models.ImageField(upload_to='stats/champion/icon', default='')
    seasons = models.ManyToManyField(Season, through='SeasonChampion')

    def __str__(self):
        return self.name

class SeasonChampion(models.Model):
    season = models.ForeignKey(Season)
    champion = models.ForeignKey(Champion)

    def get_matches(self):
        matches = PlayerMatch.objects.filter(champion=self.champion, match__series__week__season=self.season).exclude(match__duration=0)
        return matches.count()

    def get_bans(self):
        matches = TeamMatchBan.objects.filter(champion=self.champion, team__season=self.season)
        return matches.count()

    def get_winrate(self):
        matches = PlayerMatch.objects.filter(champion=self.champion, match__series__week__season=self.season).exclude(match__duration=0)
        win_ids = [o.id for o in matches if o.win()]
        num_matches = matches.count()
        if num_matches == 0:
            return 0.0
        num_wins = PlayerMatch.objects.filter(id__in=win_ids).count()
        return float(num_wins) * 100 / num_matches

    def get_most_picked_player(self):
        return PlayerMatch.objects.filter(match__series__week__season=self.season, champion=self.champion).values('player', 'team__name', 'team__icon', 'player__name').annotate(player_count=Count('player')).order_by('-player_count')[:1]
        
    def get_most_banned_by(self):
        return TeamMatchBan.objects.filter(match__series__week__season=self.season, champion=self.champion).values('team__name', 'team__icon', 'team__id').annotate(ban_count=Count('team__name')).order_by('-ban_count')[:1]
 

class Series(models.Model):
    twitch_vod_num = models.IntegerField(default=0)
    youtube_link = models.CharField(max_length=100, null=True, blank=True)
    week = models.ForeignKey(Week)
    splash = models.ImageField(upload_to='stats/champion/matchup_splashes', null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    def get_series_team_1(self):
	teamSeries = SeriesTeam.objects.filter(series=self)
	return teamSeries[0]

    def get_series_team_2(self):
	teamSeries = SeriesTeam.objects.filter(series=self)
	return teamSeries[1]

    def get_team_1(self):
	teamSeries = SeriesTeam.objects.filter(series=self)
	return teamSeries[0].team

    def get_team_2(self):
	teamSeries = SeriesTeam.objects.filter(series=self)
	return teamSeries[1].team

    def get_team_1_cast_players(self):
        return SeriesCastPlayer.objects.filter(series=self, team=self.get_team_1)

    def get_team_2_cast_players(self):
        return SeriesCastPlayer.objects.filter(series=self, team=self.get_team_2)

    def get_team_1_players(self):
        return SeriesPlayer.objects.filter(series=self, team=self.get_team_1)

    def get_team_2_players(self):
        return SeriesPlayer.objects.filter(series=self, team=self.get_team_2)

    def get_team_1_wins(self):
	return TeamMatch.objects.filter(team=self.get_team_1(), win=True, match__series=self).count()

    def get_team_2_wins(self):
	return TeamMatch.objects.filter(team=self.get_team_2(), win=True, match__series=self).count()

    def get_team_1_roster_submitted(self):
        if self.get_team_1_players().count() < 5:
            return False
        return True

    def get_team_2_roster_submitted(self):
        if self.get_team_2_players().count() < 5:
            return False
        return True

    def rosters_submitted(self):
        return self.get_team_1_roster_submitted() and self.get_team_2_roster_submitted()

    def deadline(self):
        if self.week.date is None:
            return None
        return self.week.date - datetime.timedelta(days=4)

    def past_deadline(self):
        now = datetime.datetime.now()
        if self.deadline() is not None and self.deadline() + datetime.timedelta(hours=4) < now:
            return True
        return False

    def __str__(self):
	return str(self.week) + ": " + str(self.get_team_1()) + " v " + str(self.get_team_2())


class Match(models.Model):
    id = models.BigIntegerField(primary_key=True)
    series = models.ForeignKey(Series)
    riot_id = models.BigIntegerField(default=0)
    game_num = models.IntegerField(default=1)
    tournament_code = models.CharField(max_length=100, blank=True)
    duration = models.IntegerField(default=0)

    def get_winner(self):
	return TeamMatch.objects.get(match=self, win=True)

    def get_loser(self):
	return TeamMatch.objects.get(match=self, win=False)

    def get_blue_team(self):
	return TeamMatch.objects.get(match=self, side="Blue")

    def get_red_team(self):
	return TeamMatch.objects.get(match=self, side="Red")

    def get_max_timeline_minute(self):
        if self.series.week.season.id > 2:
            playermatchtimelines = PlayerMatchTimeline.objects.filter(playermatch__match=self).annotate(minute=F('timestamp') / 1000 / 60).order_by('-minute')
            if playermatchtimelines:
                return playermatchtimelines[0].minute
            return 0
        else:
            return 0

    def __str__(self):
        seriesTeams = SeriesTeam.objects.filter(series=self.series)
        return str(seriesTeams[0].team) + " v " + str(seriesTeams[1].team) + " (" + str(self.series.week) + " game " + str(self.game_num) + ")"

    def get_timeline_diffs(self):
        return self.get_blue_team().get_timeline_diffs()

@python_2_unicode_compatible
class Player(models.Model):
    name = models.CharField(max_length=40)
    riot_id = models.IntegerField(default=0)
    matches = models.ManyToManyField(Match, through='PlayerMatch')
    photo = models.ImageField(upload_to='stats/player_photos', blank=True, null=True)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Summoner(models.Model):
    player = models.ForeignKey(Player)
    name = models.CharField(max_length=75)
    link = models.CharField(max_length=80)

    def __str__(self):
        return self.name + " (" + unicode(self.player) + ")"

class Team(models.Model):
    name = models.CharField(max_length=40)
    user = models.ForeignKey(User, default=0)
    players = models.ManyToManyField(Player, through='TeamPlayer')
    matches = models.ManyToManyField(Match, through='TeamMatch')
    season = models.ForeignKey(Season)
    icon = models.ImageField(upload_to='stats')
    splash = models.ImageField(upload_to='stats/team_splashes', default='')
    left_splash = models.ImageField(upload_to='stats/team_splashes', blank=True, null=True)
    right_splash = models.ImageField(upload_to='stats/team_splashes', blank=True, null=True)
    season_win = models.BooleanField(default=False)

    def get_players(self):
        return TeamPlayer.objects.filter(team=self, role__isFill=True)

    def get_average_match_duration(self):
        return TeamMatch.objects.filter(team=self).aggregate(Avg('match__duration'))['match__duration__avg']

    def get_average_match_duration_str(self):
        return time.strftime('%M:%S', time.gmtime(TeamMatch.objects.filter(team=self).aggregate(Avg('match__duration'))['match__duration__avg']))

    def get_average_win_duration(self):
        return TeamMatch.objects.filter(team=self, win=True).aggregate(Avg('match__duration'))['match__duration__avg']

    def get_average_win_duration_str(self):
        return time.strftime('%M:%S', time.gmtime(TeamMatch.objects.filter(team=self, win=True).aggregate(Avg('match__duration'))['match__duration__avg']))

    def get_kill_timelines(self):
        max_minute = self.get_max_timeline_minute()
        building_kills = PlayerMatchBuildingKill.objects.filter(playermatch__team=self)
        kills = PlayerMatchKill.objects.filter(killer__team=self)
        wards_placed = PlayerMatchWardPlace.objects.filter(playermatch__team=self).exclude(ward_type=Ward.objects.get(name='Undefined'))
        wards_killed = PlayerMatchWardKill.objects.filter(playermatch__team=self).exclude(ward_type=Ward.objects.get(name='Undefined'))
        results = []
        for i in range(0, max_minute):
            timestamp = i * 60000
            if self.get_num_matches() > 0:
                results.append({
                    'minute': i, 
                    'kills': 1.0 * kills.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                    'building_kills': 1.0 *building_kills.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                    'wards_placed': 1.0 * wards_placed.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                    'wards_killed': 1.0 * wards_killed.filter(timestamp__lt = timestamp).count() / self.get_num_matches()
                    })

        return results

    def get_enemy_player_matches(self):
        results = []
        for player_match in PlayerMatch.objects.filter(team=self):
            results.append(player_match.get_opponent())
        return results

    def get_killed_timelines(self):
        max_minute = self.get_max_timeline_minute()
        building_kills = PlayerMatchBuildingKill.objects.filter(playermatch__in=self.get_enemy_player_matches)
        kills = PlayerMatchKill.objects.filter(victim__team=self)
        wards_placed = PlayerMatchWardPlace.objects.filter(playermatch__in=self.get_enemy_player_matches).exclude(ward_type=Ward.objects.get(name='Undefined'))
        wards_killed = PlayerMatchWardKill.objects.filter(playermatch__in=self.get_enemy_player_matches).exclude(ward_type=Ward.objects.get(name='Undefined'))
        results = []
        for i in range(0, max_minute):
            timestamp = i * 60000
            if self.get_num_matches() > 0:
                results.append({
                    'minute': i, 
                    'kills': 1.0 * kills.filter(timestamp__lt = timestamp).count() / self.get_num_matches(), 
                    'building_kills': 1.0 * building_kills.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                    'wards_placed': 1.0 * wards_placed.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                    'wards_killed': 1.0 * wards_killed.filter(timestamp__lt = timestamp).count() / self.get_num_matches()
                    })
        return results

    def get_overall_timelines(self):
        max_minute = self.get_max_timeline_minute()
        building_kills = PlayerMatchBuildingKill.objects.filter(playermatch__team__season=self.season)
        kills = PlayerMatchKill.objects.filter(killer__team__season=self.season)
        wards_placed = PlayerMatchWardPlace.objects.filter(playermatch__team__season=self.season).exclude(ward_type=Ward.objects.get(name='Undefined'))
        wards_killed = PlayerMatchWardKill.objects.filter(playermatch__team__season=self.season).exclude(ward_type=Ward.objects.get(name='Undefined'))
        num_matches = Match.objects.filter(series__week__season=self.season).exclude(duration=0).count() * 2
        results = []
        for i in range(0, max_minute):
            timestamp = i * 60000
            if num_matches > 0:
                results.append({
                    'minute': i, 
                    'kills': 1.0 * kills.filter(timestamp__lt = timestamp).count() / num_matches, 
                    'building_kills': 1.0 * building_kills.filter(timestamp__lt = timestamp).count() / num_matches,
                    'wards_placed': 1.0 * wards_placed.filter(timestamp__lt = timestamp).count() / num_matches,
                    'wards_killed': 1.0 * wards_killed.filter(timestamp__lt = timestamp).count() / num_matches 
                    })
        return results

    def get_max_timeline_minute(self):
        if self.season.id > 2:
            ret = PlayerMatchTimeline.objects.filter(playermatch__player__team=self).annotate(minute=F('timestamp') / 1000 / 60).order_by('-minute')
            if len(ret) > 0:
                return ret[0].minute
        else:
            return 0
        return 0

    def get_record(self):
	wins = TeamMatch.objects.filter(team=self, win=True, match__series__week__regular=True).count()
	losses = TeamMatch.objects.filter(team=self, win=False, match__series__week__regular=True).exclude(match__duration=0).count()
	return str(wins) + "-" + str(losses)

    def get_sort_record(self):
	wins = TeamMatch.objects.filter(team=self, win=True, match__series__week__regular=True).exclude(match__duration=0).count()
	losses = TeamMatch.objects.filter(team=self, win=False, match__series__week__regular=True).exclude(match__duration=0).count()
        return losses - wins

    def get_top_banned(self):
        num_matches = TeamMatch.objects.filter(team=self).exclude(match__duration=0).count()
        return TeamMatchBan.objects.filter(match__teammatch__team=self).exclude(team=self).exclude(match__duration=0).values('champion', 'champion__name', 'champion__icon').annotate(ban_rate=Count('champion') * 100 / num_matches).order_by('-ban_rate')[:6]

    def get_num_matches(self):
        return TeamMatch.objects.filter(team=self).exclude(match__duration=0).count()

    def get_wins(self):
        return TeamMatch.objects.filter(team=self, win=True).exclude(match__duration=0).count()

    def get_losses(self):
        return TeamMatch.objects.filter(team=self, win=False).exclude(match__duration=0).count()

    def get_first_blood_percent(self):
        first_bloods = TeamMatch.objects.filter(team=self, first_blood=True).exclude(match__duration=0).count()
        games = TeamMatch.objects.filter(team=self).exclude(match__duration=0).count()
        if games == 0:
            return 0
        return float(first_bloods) * 100 / games

    def get_first_tower_percent(self):
        first_towers = TeamMatch.objects.filter(team=self, first_tower=True).exclude(match__duration=0).count()
        games = TeamMatch.objects.filter(team=self).exclude(match__duration=0).count()
        if games == 0:
            return 0 
        return float(first_towers) * 100 / games

    def get_tower_kills(self):
        return TeamMatch.objects.filter(team=self).aggregate(Sum('tower_kills'))

    def get_baron_kills(self):
        return TeamMatch.objects.filter(team=self).aggregate(Sum('baron_kills'))

    def __str__(self):
        return self.name + " (" + str(self.season) + ")"

class TeamRole(models.Model):
    team = models.ForeignKey(Team)
    role = models.ForeignKey(Role)

    class Meta:
        unique_together = (("team", "role"))

    def get_team_players(self):
        return TeamPlayer.objects.filter(team=self.team, role=self.role)

class SeriesTeam(models.Model):
    team = models.ForeignKey(Team)
    series = models.ForeignKey(Series)

    class Meta:
        unique_together = (("team", "series"))
    
    def get_wins(self):
	return TeamMatch.objects.filter(team=self.team, win=True, match__series=series).exclude(match__duration=0).count()    
    
    def get_record_before(self):
	wins = TeamMatch.objects.filter(team=self.team, win=True, match__series__week__regular=True, match__series__week__number__lt=self.series.week.number).count()
	losses = TeamMatch.objects.filter(team=self.team, win=False, match__series__week__regular=True, match__series__week__number__lt=self.series.week.number).exclude(match__duration=0).count()
	return str(wins) + "-" + str(losses)



class PlayerRole(models.Model):
    player = models.ForeignKey(Player)
    role = models.ForeignKey(Role)
    priority = models.IntegerField(default=10)

    class Meta:
        unique_together = (("player", "role"))

class SeriesCastTeam(models.Model):
    series = models.ForeignKey(Series)
    team = models.ForeignKey(Team)

class SeriesCastPlayer(models.Model):
    player = models.ForeignKey(Player)
    team = models.ForeignKey(Team)
    role = models.ForeignKey(Role)
    series = models.ForeignKey(Series)

class SeriesPlayer(models.Model):
    player = models.ForeignKey(Player)
    team = models.ForeignKey(Team)
    role = models.ForeignKey(Role)
    series = models.ForeignKey(Series)

class PlayerMatch(models.Model):
    player = models.ForeignKey(Player)
    match = models.ForeignKey(Match)
    role = models.ForeignKey(Role, default=0)
    team = models.ForeignKey(Team)
    participant_id = models.IntegerField(default=0)
    champion = models.ForeignKey(Champion, default=0)
    participant_id = models.IntegerField(default=0)
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    physical_damage_dealt = models.IntegerField(default=0)
    neutral_minions_killed_team_jungle = models.IntegerField(default=0)
    magic_damage_dealt = models.IntegerField(default=0)
    neutral_minions_killed_enemy_jungle = models.IntegerField(default=0)
    largest_critical_strike = models.IntegerField(default=0)
    total_damage_dealt = models.IntegerField(default=0)
    magic_damage_dealt_to_champions = models.IntegerField(default=0)
    vision_wards_bought_in_game = models.IntegerField(default=0)
    damage_dealt_to_objectives = models.IntegerField(default=0)
    largest_killing_spree = models.IntegerField(default=0)
    double_kills = models.IntegerField(default=0)
    triple_kills = models.IntegerField(default=0)
    quadra_kills = models.IntegerField(default=0)
    penta_kills = models.IntegerField(default=0)
    total_time_crowd_control_dealt = models.IntegerField(default=0)
    longest_time_spent_living = models.IntegerField(default=0)
    wards_killed = models.IntegerField(default=0)
    first_tower_assist = models.BooleanField(default=False)
    first_tower_kill = models.BooleanField(default=False)
    first_blood_assist = models.BooleanField(default=False)
    vision_score = models.IntegerField(default=0)
    wards_placed = models.IntegerField(default=0)
    turret_kills = models.IntegerField(default=0)
    damage_self_mitigated = models.IntegerField(default=0)
    champ_level = models.IntegerField(default=0)
    first_inhibitor_kill = models.BooleanField(default=False)
    gold_earned = models.IntegerField(default=0)
    magical_damage_taken = models.IntegerField(default=0)
    true_damage_taken = models.IntegerField(default=0)
    first_inhibitor_assist = models.BooleanField(default=False)
    neutral_minions_killed = models.IntegerField(default=0)
    damage_dealt_to_turrets = models.IntegerField(default=0)
    physical_damage_dealt_to_champions = models.IntegerField(default=0)
    gold_spent = models.IntegerField(default=0)
    true_damage_dealt = models.IntegerField(default=0)
    true_damage_dealt_to_champions = models.IntegerField(default=0)
    total_heal = models.IntegerField(default=0)
    total_minions_killed = models.IntegerField(default=0)
    first_blood_kill = models.BooleanField(default=False)
    sight_wards_bought_in_game = models.IntegerField(default=0)
    total_damage_dealt_to_champions = models.IntegerField(default=0)
    inhibitor_kills = models.IntegerField(default=0)
    total_damage_taken = models.IntegerField(default=0)
    killing_sprees = models.IntegerField(default=0)
    time_ccing_others = models.IntegerField(default=0)
    physical_damage_taken = models.IntegerField(default=0)

    class Meta:
        unique_together = (("player", "match"))

    def win(self):
        return self.match.get_winner().team == self.team

    def get_cs(self):
        return self.neutral_minions_killed + self.total_minions_killed

    def get_timelines(self):
        return PlayerMatchTimeline.objects.filter(playermatch=self).annotate(minute=F('timestamp') / 1000 / 60)

    def get_opponent(self):
        return PlayerMatch.objects.filter(match=self.match, role=self.role).exclude(team=self.team)[0]

class TeamPlayer(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player)
    role = models.ForeignKey(Role)
    isLeader = models.BooleanField(default=False)

    def get_player(self):
        return Player.objects.filter(pk=self.player)

    def get_team(self):
        return Team.objects.filter(pk=self.team)
    
    def get_proximity_timeline(self):
        all_timelines = PlayerMatchTimeline.objects.filter(playermatch__player=self.player, playermatch__role=self.role, playermatch__team=self.team).annotate(minute=F('timestamp') / 1000 / 60).order_by('minute')
        num_games = self.get_player_matches().count()
        results = []
        for i in range(0, 25):
            timelines = all_timelines.filter(minute=i)
            topSum = 0
            midSum = 0
            botSum = 0
            for timeline in timelines:
                #if math.hypot(timeline.position_x - 1800, timeline.position_y - 13000) < 6500:
                if timeline.position_x < 5000 and timeline.position_y > 9500:
#                    topSum = topSum + ((6000 - math.hypot(timeline.position_x - 1800, timeline.position_y - 13000)) ** 2) / 10000
                    topSum = topSum + (6500 - math.hypot(timeline.position_x - 1800, timeline.position_y - 13000)) / num_games
                if timeline.position_x > 5000 and timeline.position_x < 10500 and timeline.position_y > 4800 and timeline.position_y < 9500:
                #if math.hypot(timeline.position_x - 7500, timeline.position_y - 7500) < 5000:
#                    midSum = midSum + ((6000 - math.hypot(timeline.position_x - 7500, timeline.position_y - 7500)) ** 2) / 10000
                    midSum = midSum + (6500 - math.hypot(timeline.position_x - 7500, timeline.position_y - 7500)) / num_games
                #if math.hypot(timeline.position_x - 13000, timeline.position_y - 1800) < 6500:

                if timeline.position_x > 10500 and timeline.position_y < 4800:
#                    botSum = botSum + ((6000 - math.hypot(timeline.position_x - 13000, timeline.position_y - 1800)) ** 2) / 10000
                    botSum = botSum + (6500 - math.hypot(timeline.position_x - 13000, timeline.position_y - 1800)) / num_games
            results.append({
                'minute': i,
                'top': topSum,
                'mid': midSum,
                'bot': botSum
            })
        return results

    def get_proximity_timeline_max(self):
        timelines = self.get_proximity_timeline()

        result = 0
        for timeline in timelines:
            if max(timeline['top'], timeline['mid'], timeline['bot']) > result:
                result = max(timeline['top'], timeline['mid'], timeline['bot'])

        return result

    def get_num_matches(self):
        return PlayerMatch.objects.filter(team=self.team, player=self.player, role=self.role).count()

    def get_percent_teams_control_wards(self):
        if self.role.isFill == True:
            matches = Match.objects.filter(playermatch__player=self.player)
            match_ids = [o.id for o in matches]
    
            total_control_wards = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(control_wards=Sum('vision_wards_bought_in_game'))['control_wards']
            player_control_wards= PlayerMatch.objects.select_related().filter(player=self.player, team=self.team).aggregate(control_wards=Sum('vision_wards_bought_in_game'))['control_wards']
        else:
            matches = Match.objects.filter(playermatch__player=self.player, playermatch__role=self.role)
            match_ids = [o.id for o in matches]
    
            total_control_wards = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(control_wards=Sum('vision_wards_bought_in_game'))['control_wards']
            player_control_wards = PlayerMatch.objects.select_related().filter(player=self.player, team=self.team, role=self.role).aggregate(control_wards=Sum('vision_wards_bought_in_game'))['control_wards']

        if total_control_wards == None:
            return 0
        return 100.0 * player_control_wards / total_control_wards

    def get_percent_control_ward_gold(self):
        playermatches = self.get_player_matches().aggregate(total_gold_earned=Sum('gold_earned'), control_wards=Sum('vision_wards_bought_in_game'))
        return 100.0 * playermatches['control_wards'] * 75.0 / playermatches['total_gold_earned']

    def get_vision_timeline(self):
        max_minute = self.team.get_max_timeline_minute()
        wards_placed = PlayerMatchWardPlace.objects.filter(playermatch__team=self.team, playermatch__player=self.player, playermatch__role=self.role, ward_type__in=(Ward.objects.filter(name='Control Ward')|Ward.objects.filter(name='Yellow Trinket Ward')|Ward.objects.filter(name='Sight Ward')|Ward.objects.filter(name='Blue Trinket')))
        wards_killed = PlayerMatchWardKill.objects.filter(playermatch__team=self.team, playermatch__player=self.player, playermatch__role=self.role, ward_type__in=(Ward.objects.filter(name='Control Ward')|Ward.objects.filter(name='Yellow Trinket Ward')|Ward.objects.filter(name='Sight Ward')|Ward.objects.filter(name='Blue Trinket')))
        results = []
        for i in range(0, max_minute):
            timestamp = i * 60000
            results.append({
                'minute': i, 
                'wards_placed': 1.0 * wards_placed.filter(timestamp__lt = timestamp).count() / self.get_num_matches(),
                'wards_killed': 1.0 * wards_killed.filter(timestamp__lt = timestamp).count() / self.get_num_matches()
                })

        return results

    def get_gold_timeline(self):
        max_minute = self.team.get_max_timeline_minute()
        timelines = self.get_timelines()
        enemy_timelines = self.get_enemy_timelines()
        player_matches = self.get_player_matches()
        enemy_player_matches = self.get_enemy_player_matches()
        results = []
        total_matches = Match.objects.filter(series__week__season=self.team.season).exclude(duration=0).count() * 2

        if player_matches.count() == 0:
            return results
        for i in range(0, max_minute):
            timestamp = i * 60000
            goldSum = 0
            for player_match in player_matches:
                goldSum += PlayerMatchTimeline.objects.filter(playermatch=player_match, timestamp__lte=timestamp).order_by('-timestamp')[0].totalGold
            enemyGoldSum = 0
            for player_match in enemy_player_matches:
                enemyGoldSum += PlayerMatchTimeline.objects.filter(playermatch=player_match, timestamp__lte=timestamp).order_by('-timestamp')[0].totalGold
            goldSum /= player_matches.count()
            enemyGoldSum /= player_matches.count()
            results.append({
                'minute': i, 
                'avgGold': 1.0 * goldSum,
                'avgOppGold': 1.0 * enemyGoldSum,
                'goldDiff': 1.0 * goldSum - enemyGoldSum
                })
        return results


    def get_timelines(self):
        if self.role.isFill == True:
            timelines = PlayerMatchTimeline.objects.filter(playermatch__player=self.player, playermatch__team=self.team).annotate(minute=F('timestamp') / 1000 / 60)
        else: 
            timelines = PlayerMatchTimeline.objects.filter(playermatch__player=self.player, playermatch__team=self.team, playermatch__role=self.role).annotate(minute=F('timestamp') / 1000 / 60)
        if timelines == None:
            return None

        timelines = timelines.values('minute').annotate(avgGold=Avg('totalGold'))
        return timelines

    def get_enemy_timelines(self):
        timelines = PlayerMatchTimeline.objects.filter(playermatch__in=self.get_enemy_player_matches()).annotate(minute=F('timestamp') / 1000 / 60)

        timelines = timelines.values('minute').annotate(avgGold=Avg('totalGold'))
        return timelines

    def get_avg_vision(self):
        if self.role.isFill == True:
            avg_vision = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(avg_vision=Avg('playermatch__vision_score'))['avg_vision']
        else: 
            avg_vision = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(avg_vision=Avg('playermatch__vision_score'))['avg_vision']
        if avg_vision == None:
            return 0
        return avg_vision

    def get_avg_kills(self):
        if self.role.isFill == True:
            avg_kills = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(avg_kills=Avg('playermatch__kills'))['avg_kills']
        else: 
            avg_kills = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(avg_kills=Avg('playermatch__kills'))['avg_kills']
        if avg_kills == None:
            return 0
        return avg_kills

    def get_avg_deaths(self):
        if self.role.isFill == True:
            avg_deaths = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(avg_deaths=Avg('playermatch__deaths'))['avg_deaths']
        else:
            avg_deaths = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(avg_deaths=Avg('playermatch__deaths'))['avg_deaths']
        if avg_deaths == None:
            return 0
        return avg_deaths

    def get_avg_assists(self):
        if self.role.isFill == True:
            avg_assists = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(avg_assists=Avg('playermatch__assists'))['avg_assists']
        else:
            avg_assists = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(avg_assists=Avg('playermatch__assists'))['avg_assists']
        if avg_assists == None:
            return 0
        return avg_assists

    def get_kda(self):
        if self.role.isFill == True:
            kills = PlayerMatch.objects.filter(player=self.player, team=self.team).aggregate(sum_kills=Sum('kills'))['sum_kills']
            deaths = PlayerMatch.objects.filter(player=self.player, team=self.team).aggregate(sum_deaths=Sum('deaths'))['sum_deaths']
            assists = PlayerMatch.objects.filter(player=self.player, team=self.team).aggregate(sum_assists=Sum('assists'))['sum_assists']
        else:
            kills = PlayerMatch.objects.filter(player=self.player, team=self.team, role=self.role).aggregate(sum_kills=Sum('kills'))['sum_kills']
            deaths = PlayerMatch.objects.filter(player=self.player, team=self.team, role=self.role).aggregate(sum_deaths=Sum('deaths'))['sum_deaths']
            assists = PlayerMatch.objects.filter(player=self.player, team=self.team, role=self.role).aggregate(sum_assists=Sum('assists'))['sum_assists']

        if deaths == None:
            return 0
        if deaths == 0:
            return 1000000
        return (float(kills) + assists) / deaths

    def get_cs_per_min(self):
        if self.role.isFill == True:
            cs = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(cs=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed')) * 60.0 / F('duration')))['cs']
        else:
            cs = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(cs=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed')) * 60.0 / F('duration')))['cs']
        if cs == None:
            return 0
        return cs 

    def get_cs_per_game(self):
        if self.role.isFill == True:
            cs = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).aggregate(cs=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed'))))['cs']
        else:
            cs = Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).aggregate(cs=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed'))))['cs']
        if cs == None:
            return 0
        return cs 
    
    def get_distinct_champs_played(self):
        if self.role.isFill == True:
            return PlayerMatch.objects.filter(player=self.player, team=self.team).values('champion').aggregate(num_champs=Count('champion', distinct=True))['num_champs']
        else: 
            return PlayerMatch.objects.filter(player=self.player, team=self.team, role=self.role).values('champion').aggregate(num_champs=Count('champion', distinct=True))['num_champs']

    def get_percent_team_damage(self):
        if self.role.isFill == True:
            matches = Match.objects.filter(playermatch__player=self.player)
            match_ids = [o.id for o in matches]
    
            total_dmg_to_champs = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(dmg__sum=Sum('total_damage_dealt_to_champions'))['dmg__sum']
            player_dmg_to_champs = PlayerMatch.objects.select_related().filter(player=self.player, team=self.team).aggregate(dmg__sum=Sum('total_damage_dealt_to_champions'))['dmg__sum']
        else:
            matches = Match.objects.filter(playermatch__player=self.player, playermatch__role=self.role)
            match_ids = [o.id for o in matches]
    
            total_dmg_to_champs = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(dmg__sum=Sum('total_damage_dealt_to_champions'))['dmg__sum']
            player_dmg_to_champs = PlayerMatch.objects.select_related().filter(player=self.player, team=self.team, role=self.role).aggregate(dmg__sum=Sum('total_damage_dealt_to_champions'))['dmg__sum']

        if total_dmg_to_champs == None:
            return 0
        return 100.0 * player_dmg_to_champs / total_dmg_to_champs 

    def get_kill_participation(self):
        if self.role.isFill == True:
            matches = Match.objects.filter(playermatch__player=self.player)
            match_ids = [o.id for o in matches]
    
            total_kills = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(kills__sum=Sum('kills'))['kills__sum']
            player_kills_assists = PlayerMatch.objects.select_related().filter(player=self.player, team=self.team).aggregate(kills__sum=Sum(F('kills') + F('assists')))['kills__sum']
        else:
            matches = Match.objects.filter(playermatch__player=self.player, playermatch__role=self.role)
            match_ids = [o.id for o in matches]
    
            total_kills = PlayerMatch.objects.filter(match__id__in=match_ids, team=self.team).aggregate(kills__sum=Sum('kills'))['kills__sum']
            player_kills_assists = PlayerMatch.objects.select_related().filter(player=self.player, team=self.team, role=self.role).aggregate(kills__sum=Sum(F('kills') + F('assists')))['kills__sum']
        if player_kills_assists == None:
            return 0
        return 100.0 * player_kills_assists / total_kills

    def get_played_champion_list(self):
        if self.role.isFill == True:
            return Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team).values('playermatch__champion', 'playermatch__champion__name', 'playermatch__champion__icon').annotate(champion_count=Count('playermatch__champion'), average_vision_score=Avg('playermatch__vision_score'), avg_kills=Avg('playermatch__kills'), avg_deaths=Avg('playermatch__deaths'), avg_assists=Avg('playermatch__assists'), winrate=Avg(F('teammatch__win') * 100), cs_per_min=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed')) * 60.0 / F('duration')), average_cs=Avg(F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed'))).order_by('-champion_count')
        else:
            return Match.objects.select_related().filter(playermatch__player=self.player, teammatch__team=self.team, playermatch__role=self.role).values('playermatch__champion', 'playermatch__champion__name', 'playermatch__champion__icon').annotate(champion_count=Count('playermatch__champion'), average_vision_score=Avg('playermatch__vision_score'), avg_kills=Avg('playermatch__kills'), avg_deaths=Avg('playermatch__deaths'), avg_assists=Avg('playermatch__assists'), winrate=Avg(F('teammatch__win') * 100), cs_per_min=Avg((F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed')) * 60.0 / F('duration')), average_cs=Avg(F('playermatch__neutral_minions_killed') + F('playermatch__total_minions_killed')), wins=Sum('teammatch__win'), losses=ExpressionWrapper(Count('playermatch__champion') - Sum('teammatch__win'), output_field=models.IntegerField())).order_by('-champion_count')

    def get_player_matches(self):
        if self.role.isFill == True:
            return PlayerMatch.objects.filter(player=self.player, team=self.team)
        else:
            return PlayerMatch.objects.filter(player=self.player, team=self.team, role=self.role)

    def get_enemy_player_matches(self):
        results = []
        for player_match in self.get_player_matches():
            results.append(player_match.get_opponent())
        return results

    def get_cs_diff_at_15(self):
        if self.team.season.id < 3:
            return 0
        player_matches = self.get_player_matches()
        result = 0
        for playermatch in player_matches:
            timeline = PlayerMatchTimeline.objects.filter(playermatch=playermatch, timestamp__lt=910000).values('timestamp', 'minions_killed', 'monsters_killed', 'playermatch').annotate(cs=F('minions_killed')+F('monsters_killed')).order_by('-timestamp')[0]
            enemy_timeline = PlayerMatchTimeline.objects.filter(playermatch__match=playermatch.match, playermatch__role=playermatch.role, timestamp__lt=910000).exclude(playermatch__team=playermatch.team).values('timestamp', 'minions_killed', 'monsters_killed', 'playermatch').annotate(cs=F('minions_killed')+F('monsters_killed')).order_by('-timestamp')[0]
            result = result + timeline['cs'] - enemy_timeline['cs']
        if player_matches.count() == 0:
            return 0.0
        return 1.0 * result / player_matches.count()

class TeamMatch(models.Model):
    team = models.ForeignKey(Team)
    match = models.ForeignKey(Match)
    side = models.CharField(max_length=5)
    win = models.BooleanField(default=False)
    first_dragon = models.BooleanField(default=False)
    first_inhibitor = models.BooleanField(default=False)
    baron_kills = models.IntegerField(default=0)
    first_rift_herald = models.BooleanField(default=False)
    first_blood = models.BooleanField(default=False)
    first_tower = models.BooleanField(default=False)
    inhibitor_kills = models.IntegerField(default=0)
    tower_kills = models.IntegerField(default=0)

    class Meta:
        unique_together = (("team", "match"))

    def get_player_matches(self):
        return PlayerMatch.objects.filter(match=self.match, team=self.team)

    def get_team_bans(self):
        return TeamMatchBan.objects.filter(match=self.match, team=self.team).order_by('-pickTurn')

    def get_timelines(self):
        return PlayerMatchTimeline.objects.filter(playermatch__match=self.match, playermatch__team=self.team).annotate(minute=F('timestamp') / 1000 / 60).values('minute').annotate(sumGold=Sum('totalGold'))

    def get_enemy_timelines(self):
        return PlayerMatchTimeline.objects.filter(playermatch__match=self.match).exclude(playermatch__team=self.team).annotate(minute=F('timestamp') / 1000 / 60).values('minute').annotate(sumGold=Sum('totalGold'))

    def get_timeline_diffs(self):
        enemy_timelines = self.get_enemy_timelines()
        gold_diff_timelines = []
        for timeline in self.get_timelines():
            gold_diff_timelines.append({'minute': timeline['minute'], 'sumGold': timeline['sumGold'] - enemy_timelines.get(minute=timeline['minute'])['sumGold']})
        return gold_diff_timelines





class TeamMatchBan(models.Model):
    team = models.ForeignKey(Team)
    match = models.ForeignKey(Match)
    champion = models.ForeignKey(Champion)
    pickTurn = models.IntegerField(default=0)

    class Meta:
        ordering = ["champion"]

class Item(models.Model):
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=5000)
    icon = models.ImageField(upload_to='stats/item/icon', default='')

class PlayerMatchItem(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    item = models.ForeignKey(Item)

class Lane(models.Model):
    name = models.CharField(max_length=10)
    riot_name = models.CharField(max_length=25)

    def __str__(self):
        return self.name

class Ward(models.Model):
    name = models.CharField(max_length=25)
    riot_name = models.CharField(max_length=25)

    def __str__(self):
        return self.name

class Building(models.Model):
    lane = models.ForeignKey(Lane)
    name = models.CharField(max_length=25)
    riot_name = models.CharField(max_length=25)
    riot_subname = models.CharField(max_length=25, default="")
    
    def __str__(self):
        return str(self.lane) + ' ' + self.name

class EliteMonster(models.Model):
    name = models.CharField(max_length=25)
    riot_name = models.CharField(max_length=25)
    riot_subname = models.CharField(max_length=25, default="")

    def __str__(self):
        return self.name

class PlayerMatchKill(models.Model):
    killer = models.ForeignKey(PlayerMatch)
    victim = models.ForeignKey(PlayerMatch, related_name="victim")
    timestamp = models.IntegerField()

class PlayerMatchAssist(models.Model):
    kill = models.ForeignKey(PlayerMatchKill)
    playermatch = models.ForeignKey(PlayerMatch)

class PlayerMatchWardPlace(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    ward_type = models.ForeignKey(Ward)
    timestamp = models.IntegerField()

class PlayerMatchWardKill(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    ward_type = models.ForeignKey(Ward)
    timestamp = models.IntegerField()

class PlayerMatchBuildingKill(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    building_type = models.ForeignKey(Building)
    timestamp = models.IntegerField()

class PlayerMatchBuildingAssist(models.Model):
    kill = models.ForeignKey(PlayerMatchBuildingKill)
    playermatch = models.ForeignKey(PlayerMatch)

class PlayerMatchEliteMonsterKill(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    monster_type = models.ForeignKey(EliteMonster)
    timestamp = models.IntegerField()

class PlayerMatchTimeline(models.Model):
    playermatch = models.ForeignKey(PlayerMatch)
    timestamp = models.IntegerField()
    level = models.IntegerField(default=1)
    gold = models.IntegerField(default=0)
    totalGold = models.IntegerField(default=0)
    minions_killed = models.IntegerField(default=0)
    monsters_killed = models.IntegerField(default=0)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)

class SummonerSpell(models.Model):
    riot_id = models.IntegerField(default=0)
    name = models.CharField(max_length=20)
    icon = models.ImageField(upload_to='stats/summoner-spell/icon', default='')

class PlayerMatchSummonerSpell(models.Model):
    player = models.ForeignKey(Player)
    match = models.ForeignKey(Match)
    summoner_spell = models.ForeignKey(SummonerSpell)


class MatchCaster(models.Model):
    match = models.ForeignKey(Match)
    player = models.ForeignKey(Player)

class HypeVideo(models.Model):
    season = models.ForeignKey(Season)
    creator = models.ForeignKey(Player)
    youtube_link = models.CharField(max_length=100, default='')



# PAGE STUFF

class HomePageCarouselObject(models.Model):
    number = models.IntegerField(unique=True, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    splash = models.ImageField(upload_to='stats/carousel_images', blank=True, null=True)

    def __str__(self):
        return "Carousel Position " + str(self.number)



#class HomePagePosition(models.Model):
#    number = models.IntegerField(unique=True)
#
#    def __str__(self):
#        return "Home Page Position " + str(self.number)
#
#class HomePageStaticImage(models.Model):
#    position = models.ForeignKey(HomePagePosition, blank=True, null=True)
#    image = models.ImageField(upload_to='stats/announcement_splashes', default='', blank=True, null=True)
#    style = models.CharField(max_length=100, default="")
#
#    def __str__(self):
#        return "Image at " + str(self.position)
#
#class HomePageStaticContent(models.Model):
#    position = models.ForeignKey(HomePagePosition, blank=True, null=True)
#    content = models.FileField(upload_to='stats/articles', blank=True, null=True)
#
#    def __str__(self):
#        return "Content at " + str(self.position)
#
#class HomePageCarousel(models.Model):
#    position = models.ForeignKey(HomePagePosition, blank=True, null=True)
#
#    def __str__(self):
#        return "Carousel at " + str(self.position)
#
#class HomePageSchedule(models.Model):
#    position = models.ForeignKey(HomePagePosition, blank=True, null=True)
#    season = models.ForeignKey(Season)
#
#    def __str__(self):
#        return "Schedule for Season " + str(self.season.id) + " at " + str(self.position)
#
#class HomePageCarouselPosition(models.Model):
#    number = models.IntegerField()
#    carousel = models.ForeignKey(HomePageCarousel)
#
#    class Meta:
#        unique_together = (("number", "carousel"))
#
#    def __str__(self):
#        return "Carousel at " + str(self.carousel.position) + ": Position " + str(self.number)


class ArticlePage(models.Model):
    url_name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    synopsis = models.CharField(max_length=100)
    youtube_link = models.CharField(max_length=100, blank=True, null=True)
    content = models.FileField(upload_to='stats/articles', blank=True, null=True)
    splash = models.ImageField(upload_to='stats/announcement_splashes', default='', blank=True, null=True)
    header = models.ImageField(upload_to='stats/announcement_headers', default='', blank=True, null=True)
    team_tag = models.ManyToManyField(Team)

    def clean_content(self):
        if self.content:
            file_content = self.content.read()
            cleanr = re.compile('<.*?>')
            cleantext = re.sub(cleanr, '', file_content)
            cleantext = cleantext.strip('\n')
            cleantext = cleantext.strip('\t')
            return cleantext
        else:
            return ""

    def __str__(self):
        return self.title

