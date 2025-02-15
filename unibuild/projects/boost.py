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
import os

from config import config
from unibuild import Project
from unibuild.modules import b2, build, Patch, urldownload
from unibuild.projects import python
import patch

boost_version = config['boost_version']
boost_tag_version = ".".join([_f for _f in [boost_version, config['boost_version_tag']] if _f])
boost_path = "{}/boost_{}".format(config["paths"]["build"], boost_tag_version.replace(".", "_"))
python_version = config['python_version']
vc_version = config['vc_version_for_boost']

boost_components = ["date_time",
    "coroutine",
    "filesystem",
    "thread",
    "log",
    "locale"]
boost_components_shared = ["python"]

user_config_jam = "user-config-{}.jam".format("64" if config['architecture'] == "x86_64" else "32")

config_template = ("using python\n"
                   "  : {0}\n"
                   "  : {1}/python.exe\n"
                   "  : {2}/Include\n"
                   "  : {1}\n"
                   "  : <address-model>{3}\n"
                   "  : <define>BOOST_ALL_NO_LIB=1\n"
                   "  ;")


def patchboost(context):
    try:
        savedpath = os.getcwd()
        os.chdir(boost_path)
        pset = patch.fromfile(os.path.join(config['__Umbrella_path'], "patches", "boost_python_libname.patch"))
        pset.apply()
        os.chdir(savedpath)
        return True
    except OSError:
        return False

if config.get('binary_boost', True):
    boost_prepare = Project("boost_prepare")
    if vc_version == '14.1':
        boost = Project("boost").depend(urldownload.URLDownload("https://github.com/247321453/modorganizer-umbrella/releases/download/1.2-141/boost_prebuilt_{}.7z"
                                                        .format(boost_tag_version.replace(".", "_"))).set_destination("boost_{}".format(boost_tag_version.replace(".", "_"))))
    else:
        boost = Project("boost").depend(urldownload.URLDownload("https://github.com/247321453/modorganizer-umbrella/releases/download/1.1/boost_prebuilt_{}.7z"
                                                        .format(boost_tag_version.replace(".", "_"))).set_destination("boost_{}".format(boost_tag_version.replace(".", "_"))))
    if config['architecture'] == 'x86_64':
        boost_stage = Patch.Copy(os.path.join("{}/lib{}-msvc-{}/lib/boost_python{}-vc{}-mt-{}-{}.dll"
                                              .format(boost_path,
                                                      "64" if config['architecture'] == 'x86_64' else "32",
                                                      vc_version,
                                                      config["python_version"].replace(".", ""),
                                                      vc_version.replace(".", ""),
                                                      "x64" if config['architecture'] == "x86_64" else "x86",
                                                      "_".join(boost_version.split(".")[:-1]))),
                                 os.path.join(config["paths"]["install"], "bin"))
        boost.depend(boost_stage)


else:
    boost_prepare = Project("boost_prepare") \
        .depend(b2.Bootstrap()
                .depend(Patch.CreateFile(user_config_jam,
                                         lambda: config_template.format(
                                             python_version,
                                             os.path.join(
                                                python.python['build_path'], "PCBuild",
                                                "{}".format("" if config['architecture'] == 'x86' else "amd64"))
                                             .replace("\\", '/'),
                                             os.path.join(python.python['build_path']).replace("\\", '/'),
                                             "64" if config['architecture'] == "x86_64" else "32"))
                        .depend(urldownload.URLDownload("https://dl.bintray.com/boostorg/release/{}/source/boost_{}.7z"
                                                        .format(boost_version,boost_tag_version.replace(".", "_"))
                                                         , tree_depth=1)
                                .set_destination("boost_{}".format(boost_tag_version.replace(".", "_"))))))

    if config['architecture'] == 'x86_64':
    # This is a convient way to make each boost flavors we build have these dependencies:
        boost_prepare.depend("Python")

    boost = Project("boost")

    if config['architecture'] == 'x86_64':
        boost_stage = Patch.Copy(os.path.join("{}/lib{}-msvc-{}/lib/boost_python{}-vc{}-mt-{}-{}.dll"
                                              .format(boost_path,
                                                      "64" if config['architecture'] == 'x86_64' else "32",
                                                      vc_version,
                                                      config["python_version"].replace(".", ""),
                                                      vc_version.replace(".", ""),
                                                      "x64" if config['architecture'] == "x86_64" else "x86",
                                                      "_".join(boost_version.split(".")[:-1]))),
                                 os.path.join(config["paths"]["install"], "bin"))
        boost.depend(boost_stage)
    else:
        boost_stage = boost

    with_for_all = ["--with-{0}".format(component) for component in boost_components]
    with_for_shared = ["--with-{0}".format(component) for component in boost_components_shared]
    commonargs = ["address-model={}".format("64" if config['architecture'] == 'x86_64' else "32"),
        "-a",
        "--user-config={}".format(os.path.join(boost_path,user_config_jam)),
        "-j {}".format(config['num_jobs']),
        "toolset=msvc-" + vc_version,
        "--stagedir=lib{}-msvc-{}".format("64" if config['architecture'] == 'x86_64' else "32",vc_version),
        "--libdir=lib{}-msvc-{}".format("64" if config['architecture'] == 'x86_64' else "32",vc_version)]

    if config['architecture'] == 'x86_64':
        b2tasks = [("Shared", ["link=shared"] + with_for_all + with_for_shared),
                   ("Static", ["link=static", "runtime-link=shared"] + with_for_all),
                   ("StaticCRT64", ["link=static", "runtime-link=static"] + with_for_all)]
    else:
        b2tasks = [("StaticCRT32", ["link=static", "runtime-link=static"] + with_for_all)]

    for (taskname, taskargs) in b2tasks:
        boost_stage.depend(b2.B2(taskname,boost_path).arguments(commonargs + taskargs)
            .depend(boost_prepare))
