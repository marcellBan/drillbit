# -*- coding: utf-8 -*-
"""
Local data manager for the slack bot
"""

import sys
import os

_DATA_FILE = "data/{}.db".format("teams")
_REGISTERED_INDICATOR = "reg"
_ADMINS_INDICATOR = "adm"
_REGISTERED_SECTION_STR = "[SECTION REGISTERED]"
_ADMINS_SECTION_STR = "[SECTION ADMINS]"
_SECTION_END_STR = "[END SECTION]"


class DataManager(object):
    """
    Instanciates a data manager object to manage all local data for the bot
    (Registered students, Admins, Questions, Answers)
    """

    def __init__(self, team_id):
        # FIXME: do I need this?
        # super(DataManager, self).__init__()
        self.team_id = team_id
        self._dbfile = "data/{}.db".format(team_id)
        try:
            with open(self._dbfile) as infile:
                self._parse_dbfile(infile)
        except ValueError:
            print "Error while parsing file: {}".format(self._dbfile)
        except:
            self._registered_users = list()
            self._admins = list()

    def _parse_dbfile(self, infile):
        """
        parses a database file and loads it's contents into memory
        """
        fail = False
        section = None
        self._registered_users = list()
        self._admins = list()
        for line in infile:
            section, sectionC, fail = self._check_for_section(section, line)
            if fail:
                raise ValueError()
            if not sectionC and section is not None:
                self._parse_data_line(line, section)
        if section is not None:
            raise ValueError()

    def _parse_data_line(self, line, section):
        """
        parses a single line containing data
        """
        # TODO: implement me

    def _check_for_section(self, section, line):
        """
        checks whether the current line is a section indicator
        """
        new_section = section
        section_change = False
        fail = False
        if line == _REGISTERED_SECTION_STR:
            if section is None:
                new_section = _REGISTERED_INDICATOR
                section_change = True
            else:
                fail = True
        elif line == _ADMINS_SECTION_STR:
            if section is None:
                new_section = _ADMINS_INDICATOR
                section_change = True
            else:
                fail = True
        elif line == _SECTION_END_STR:
            if section is not None:
                new_section = None
                section_change = True
            else:
                fail = True
        return new_section, section_change, fail

    def register_user(self, user_id):
        """
        registers a user id in the database for participation
        """
        self._registered_users.append(user_id)
        # TODO: save changes to file

    def get_registered_users(self):
        """
        returns a list of registered user ids
        """
        return self._registered_users

    def get_admins(self):
        """
        returns a list of user ids with admin rights
        """
        return self._admins


def load_dbs():
    """
    loads a set of authed teams' credentials and their db files
    returns a dict of Data_manager objects a dictionary of authed teams and a current team id
    """
    dbs = dict()
    authed_teams = dict()
    current_team = None
    # TODO: make it safer
    try:
        with open(_DATA_FILE) as infile:
            for line in infile:
                parts = line.split()
                authed_teams[parts[0]] = {"bot_token": parts[1]}
    except:
        pass
    for team in authed_teams:
        dbs[team] = DataManager(team)
        current_team = team
    return dbs, authed_teams, current_team


def save_dbs(teams=None, dbs=None):
    if teams is not None:
        with open(_DATA_FILE, "w") as teams_file:
            for team in teams:
                teams_file.write("{} {}\n".format(team, teams[team]["bot_token"]))
    if dbs is not None:
        # TODO: save team dbs
        pass
