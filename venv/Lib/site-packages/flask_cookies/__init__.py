#!/usr/bin/env python
# coding=utf8

from flask import Blueprint
from warnings import warn


class Cookies(object):
    def __init__(self, GTM_ID=None, app=None):
        if app is not None:
            self.init_app(app)
        self.GTM_ID = GTM_ID
        if not GTM_ID:
            GTM_ID_WARNING = '''\033[93m You must pass your Google Tag Manager ID to Cookies() initialization or it will \033[4mNOT be connected with your GTM account\033[0m\033[93m: "cookies = Cookies(<put-here-your-GTM-ID>)"\033[0m '''
            warn(GTM_ID_WARNING)
            # raise ValueError()

    def init_app(self, app):

        blueprint = Blueprint(
            'cookies',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/cookies')

        def pass_gtm_id():
            '''
                this is to pass GTM ID without recording it
                in plain code
            '''
            return self.GTM_ID

        @app.context_processor
        def inject_user_gtmID():
            '''
                pass the environmental variable GTM ID to all pages
            '''
            pass_gtm_id_dict = dict()
            pass_gtm_id_dict.update(pass_gtm_id=pass_gtm_id)
            return pass_gtm_id_dict

        app.register_blueprint(blueprint)
