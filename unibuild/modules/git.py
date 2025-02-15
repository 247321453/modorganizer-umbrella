# Copyright (C) 2015 Sebastian Herbord.  All rights reserved.
# Copyright (C) 2016 - 2019 Mod Organizer contributors.
#
# This file is part of Mod Organizer.
#
# Mod Organizer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mod Organizer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mod Organizer.  If not, see <http://www.gnu.org/licenses/>.
import logging
import os
import subprocess

from config import config
from unibuild.modules.repository import Repository
from unibuild import Task

def Popen(cmd, **kwargs):
    pc = ''
    if 'cwd' in kwargs:
        pc += os.path.relpath(kwargs['cwd'],os.path.abspath('..'))
    pc += '>'
    for arg in cmd:
        pc += ' ' + arg
    print(pc)
    return subprocess.Popen(cmd,**kwargs)

class SuperRepository(Task):
    def __init__(self, name):
        super(SuperRepository, self).__init__()
        self.__name = name
        self.__context_data = {}
        self.prepare()

    def prepare(self):
        self.__context_data['build_path'] = os.path.join(config["paths"]["build"], self.__name)

    @property
    def path(self):
        return self.__context_data['build_path']

    @property
    def name(self):
        return self.__name

    def __getitem__(self, key):
        return self.__context_data[key]

    def __setitem__(self, key, value):
        self.__context_data[key] = value

    def __contains__(self, keys):
        return self.__context_data.__contains__(keys)

    def process(self, progress):
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        is_initialised_process = Popen([config['paths']['git'], "rev-parse", "--is-inside-work-tree"], cwd=self.path, env=config['__environment'], stdout=subprocess.PIPE)
        (is_initialised_stdout, is_initialised_stderr) = is_initialised_process.communicate()
        if is_initialised_stdout.strip() != "true":
            proc = Popen([config['paths']['git'], "init"],
                         cwd=self.path,
                         env=config['__environment'])
            proc.communicate()
            if proc.returncode != 0:
                logging.error("failed to init superproject %s (returncode %s)", self._name, proc.returncode)
                return False
        return True


class Clone(Repository):
    def __init__(self, url, branch, super_repository=None, update=True, commit=None, shallowclone=False):
        if config['shallowclone']:
            self.shallowclone = True
        super(Clone, self).__init__(url, branch)
        self.__super_repository = super_repository
        self.__base_name = os.path.basename(self._url)
        self.__update = update
        self.__commit = commit
        self.__shallowclone = shallowclone
        if self.__super_repository is not None:
            self._output_file_path = os.path.join(self.__super_repository.path, self.__determine_name())
            self.depend(super_repository)

    def __determine_name(self):
        return self.__base_name

    def prepare(self):
        self._context['build_path'] = self._output_file_path

    def process(self, progress):
        proc = None
        if os.path.exists(os.path.join(self._output_file_path, ".git")):
            if self.__update and not config.get('offline', False):
                if self.__shallowclone:
                    proc = Popen([config['paths']['git'], "pull", "--recurse-submodules", self._url, self._branch],
                             cwd=self._output_file_path,
                             env=config["__environment"])
                else:
                    proc = Popen([config['paths']['git'], "pull", "--recurse-submodules", self._url, self._branch],
                             cwd=self._output_file_path,
                             env=config["__environment"])
        else:
            if self.__super_repository is not None:
                if self.__shallowclone:
                    proc = Popen([config['paths']['git'], "submodule", "add", "--depth", "1", "-b", self._branch,
                              "--force", "--name", self.__base_name,
                              self._url, self.__base_name],
                             cwd=self.__super_repository.path,
                             env=config['__environment'])
                else:
                    proc = Popen([config['paths']['git'], "submodule", "add", "-b", self._branch,
                                  "--force", "--name", self.__base_name,
                                  self._url, self.__base_name
                                  ],
                            cwd=self.__super_repository.path,
                            env=config['__environment'])
            else:
                if self.__shallowclone:
                    proc = Popen([config['paths']['git'], "clone", "--recurse-submodules","--depth", "1",
                                  "-b", self._branch, self._url, self._context["build_path"]],
                                env=config["__environment"])
                else:
                    proc = Popen([config['paths']['git'], "clone", "--recurse-submodules",
                                  "-b", self._branch, self._url, self._context["build_path"]],
                                  env=config["__environment"])

        if proc is not None:
            proc.communicate()
            if proc.returncode != 0:
                logging.error("failed to clone repository %s (returncode %s)", self._url, proc.returncode)
                return False

        if self.__commit is not None:
            if self.__shallowclone:
                proc = Popen([config['paths']['git'], "checkout","--depth", "1", self.__commit],
                         cwd=self._context["build_path"],
                         env=config["__environment"])
            else:
                proc = Popen([config['paths']['git'], "checkout", self.__commit],
                         cwd=self._context["build_path"],
                         env=config["__environment"])

            if proc is not None:
                proc.communicate()
                if proc.returncode != 0:
                    logging.error("failed to checkout repository %s (returncode %s)", self._url, proc.returncode)
                    return False

        return True

    @staticmethod
    def _expiration():
        return config.get('repo_update_frequency', 60 * 60 * 24)  # default: one day

    def set_destination(self, destination_name):
        self.__base_name = destination_name.replace("/", os.path.sep)
        if self.__super_repository is not None:
            self._output_file_path = os.path.join(self.__super_repository.path, self.__base_name)
        else:
            self._output_file_path = os.path.join(config["paths"]["build"], self.__base_name)
        return self
