# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
"""

import os
import data_manager

from slackclient import SlackClient


class Bot(object):
    """ Instanciates a Bot object to handle Slack quiz interactions."""

    def __init__(self):
        super(Bot, self).__init__()
        self.dbs, self.authed_teams, self.current_team = data_manager.load_dbs()
        # FIXME: do I need these?
        self.name = "drill_bit_bot"
        # self.emoji = ":robot_face:"
        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
                      "client_secret": os.environ.get("CLIENT_SECRET"),
                      "scope": "bot"}
        self.verification = os.environ.get("VERIFICATION_TOKEN")

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
        self.client = SlackClient("") if self.current_team is None else\
            SlackClient(self.authed_teams[self.current_team]["bot_token"])

    def auth(self, code):
        """
        Exchanges the temporary auth code for an OAuth token and sets current team
        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpoint
        auth_response = self.client.api_call(
            "oauth.access",
            client_id=self.oauth["client_id"],
            client_secret=self.oauth["client_secret"],
            code=code
        )
        self.current_team = auth_response["team_id"]
        self.authed_teams[self.current_team] = {"bot_token":
                                                auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's bot token
        self.client = SlackClient(self.authed_teams[self.current_team]["bot_token"])
        if not self.dbs.get(self.current_team):
            self.dbs[self.current_team] = data_manager.DataManager(self.current_team)
        # TODO: save authed teams
        data_manager.save_dbs(teams=self.authed_teams)

    def open_dm(self, user_id):
        """
        open a DM for sending quiz questions to users
        gets the id of the user to send the question to
        returns the id of the DM channel opened by this method
        """
        new_dm = self.client.api_call("im.open", user=user_id)
        dm_id = new_dm["channel"]["id"]
        return dm_id

    def change_team_to_users_team(self, user_id):
        """
        Changes the current team to the team that the given user is a member of\n
        and connects to Slack with the appropiate credentials
        """
        if self.user_is_in_current_team(user_id):
            return
        for team in self.authed_teams:
            self.current_team = team
            self.client = SlackClient(self.authed_teams[self.current_team]["bot_token"])
            if self.user_is_in_current_team(user_id):
                return

    def user_is_in_current_team(self, user_id):
        """
        returns whether the given user is in the current team
        """
        call = self.client.api_call("users.list")
        for member in call["members"]:
            if member["id"] == user_id:
                return True
        return False

    def is_registered(self, user_id):
        """
        returns whether the given user is registered or not
        """
        for member in self.dbs[self.current_team].get_registered_users():
            if member == user_id:
                return True
        return False

    def get_user_ids(self, users):
        """
        given a list of usernames
        returns a list of the corresponding user_ids in the current team
        """
        user_ids = list()
        for member in self.client.api_call("users.list")["members"]:
            if member["name"] in users:
                user_ids.append(member["id"])
        return user_ids

    def is_user_admin(self, user_id):
        """
        returns whether the given user has admin priviliges or not
        """
        for member in self.dbs[self.current_team].get_admins():
            if member == user_id:
                return True
        return False

    def handle_registration(self, user, text):
        """
        handles registration queries
        """
        # self registration
        if text == "!register" and not self.is_registered(user):
            self.dbs[self.current_team].register_user(user)
        # admin registers user(s) by name
        elif self.is_user_admin(user):
            users = text.split()[1:]
            user_ids = self.get_user_ids(users)
            for user_id in user_ids:
                if not self.is_registered(user_id):
                    self.dbs[self.current_team].register_user(user_id)

    def handle_message(self, slack_message_event):
        """
        Distributes all message events (DMs, channel messages) to get handled
        """
        print(slack_message_event)
        text = slack_message_event["event"]["text"]
        user = None
        if slack_message_event["event"].get("user"):
            user = slack_message_event["event"]["user"]
        channel = slack_message_event["event"]["channel"]
        self.change_team_to_users_team(user)
        # new registration query
        if text.startswith("!register"):
            self.handle_registration(user, text)
        elif user is not None:
            dmid = self.open_dm(user)
            self.client.api_call("chat.postMessage",
                                 channel=dmid,
                                 username=self.name,
                                 text="Szevasz!")
        return True
