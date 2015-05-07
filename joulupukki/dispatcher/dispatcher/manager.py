import logging
import pecan
import time

from joulupukki.dispatcher.dispatcher.dispatcher import Dispatcher
from joulupukki.common.datamodel.build import Build
from joulupukki.common.datamodel.project import Project
from joulupukki.common.datamodel.user import User
from joulupukki.common.database import mongo
from joulupukki.common.carrier import Carrier


class Manager(object):
    def __init__(self, app):
        self.must_run = False
        self.app = app
        self.build_list = {}
        self.carrier = Carrier(pecan.conf.rabbit_server,
                               pecan.conf.rabbit_port,
                               pecan.conf.rabbit_user,
                               pecan.conf.rabbit_password,
                               pecan.conf.rabbit_vhost,
                               pecan.conf.rabbit_db)
        self.carrier.declare_queue('builds.queue')

    def shutdown(self):
        logging.debug("Stopping Manager")
        self.carrier.closing = True
        self.must_run = False

    def run(self):
        self.must_run = True
        logging.debug("Starting Manager")

        while self.must_run:
            time.sleep(0.1)
            new_build = self.carrier.get_message('builds.queue')
            build = None
            if new_build is not None:
                build = Build(new_build)
                if build:
                    build.user = User.fetch(new_build['username'],
                                        sub_objects=False)
                    build.project = Project.fetch(build.username,
                                              new_build['project_name'],
                                              sub_objects=False)
                    logging.debug("Task received")
                    build.set_status("dispatching")
                    dispatcher = Dispatcher(build)
                    self.build_list[dispatcher.uuid2] = dispatcher
                    dispatcher.start()

            self.check_builds_status()

    def check_builds_status(self):
        builds = mongo.builds.find({"status": "building"})
        for b in builds:
            finished = 0
            build = Build(b)
            jobs = build.get_jobs()
            if len(jobs) == build.job_count:
                for job in jobs:
                    if job.status == 'succeeded':
                        finished += 1
                    elif job.status == 'failed':
                        build.set_status('failed')

                if finished == len(jobs):
                    build.finishing()
