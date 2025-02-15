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
import os.path
import shutil

from config import config
from string import Formatter
from glob import glob
from unibuild import Project
from unibuild.modules import build, cmake, git, github, urldownload, msbuild, appveyor
from unibuild.projects import boost, googletest, libloot, lz4, nasm, ncc, openssl, sevenzip, sip, usvfs, python, pyqt5, qt5, zlib, nuget
from unibuild.utility import FormatDict
from unibuild.utility.config_utility import cmake_parameters, qt_inst_path

tl_repo = git.SuperRepository("modorganizer_super")


def gen_userfile_content(project):
    with open("CMakeLists.txt.user.template", 'r') as f:
        res = Formatter().vformat(f.read(), [], FormatDict({
            'build_dir': project['edit_path'],
            'environment_id': config['qt_environment_id'],
            'profile_name': config['qt_profile_name'],
            'profile_id': config['qt_profile_id']
        }))
        return res


for author, git_path, path, branch, dependencies, Build in [
    (config['Main_Author'], "modorganizer-game_features", "game_features", config['Main_Branch'], [], False),
    (config['Main_Author'], "modorganizer-archive", "archive", config['Main_Branch'], ["7zip", "Qt5", "boost"], True),
    (config['Main_Author'], "modorganizer-uibase", "uibase", config['Main_Branch'], ["Qt5", "boost"], True),
    (config['Main_Author'], "modorganizer-lootcli", "lootcli", config['Main_Branch'], ["libloot", "boost"], True),
    (config['Main_Author'], "modorganizer-esptk", "esptk", config['Main_Branch'], ["boost"], True),
    (config['Main_Author'], "modorganizer-bsatk", "bsatk", config['Main_Branch'], ["zlib", "boost", "lz4"], True),
    (config['Main_Author'], "modorganizer-nxmhandler", "nxmhandler", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-helper", "helper", config['Main_Branch'], ["Qt5","boost"], True),
    (config['Main_Author'], "modorganizer-game_gamebryo", "game_gamebryo", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                   "modorganizer-game_features",
                                                                                                   "lz4"], True),
    (config['Main_Author'], "modorganizer-game_oblivion", "game_oblivion", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                   "modorganizer-game_gamebryo",
                                                                                                   "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_fallout3", "game_fallout3", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                   "modorganizer-game_gamebryo",
                                                                                                   "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_fallout4", "game_fallout4", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                   "modorganizer-game_gamebryo",
                                                                                                   "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_fallout4vr", "game_fallout4vr", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                       "modorganizer-game_gamebryo",
                                                                                                       "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_falloutnv", "game_falloutnv", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                                     "modorganizer-game_gamebryo",
                                                                                                     "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_morrowind", "game_morrowind", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                    "modorganizer-game_gamebryo",
                                                                                    "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_skyrim", "game_skyrim", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                  "modorganizer-game_gamebryo",
                                                                                  "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_skyrimse", "game_skyrimse", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                  "modorganizer-game_gamebryo",
                                                                                  "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_skyrimvr", "game_skyrimvr", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                  "modorganizer-game_gamebryo",
                                                                                  "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_ttw", "game_ttw", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                         "modorganizer-game_gamebryo",
                                                                                         "modorganizer-game_features"], True),
    ('247321453', "modorganizer-game_monsterhunterworld", "game_monsterhunterworld", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                         "modorganizer-game_gamebryo",
                                                                                         "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-game_enderal", "game_enderal", config['Main_Branch'], ["Qt5", "modorganizer-uibase",
                                                                                         "modorganizer-game_gamebryo",
                                                                                         "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-tool_inieditor", "tool_inieditor", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-tool_inibakery", "tool_inibakery", config['Main_Branch'], ["modorganizer-uibase", "modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-tool_configurator", "tool_configurator", config['Main_Branch'], ["PyQt5"], True),
    (config['Main_Author'], "modorganizer-fnistool", "fnistool", config['Main_Branch'],  ["PyQt5"], True),
    (config['Main_Author'], "modorganizer-preview_base", "preview_base", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-diagnose_basic", "diagnose_basic", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-script_extender_plugin_checker", "script_extender_plugin_checker", config['Main_Branch'],  ["PyQt5"], True),
    (config['Main_Author'], "modorganizer-check_fnis", "check_fnis", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-installer_bain", "installer_bain", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-installer_manual", "installer_manual", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-installer_bundle", "installer_bundle", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-installer_quick", "installer_quick", config['Main_Branch'], ["Qt5", "modorganizer-uibase"], True),
    (config['Main_Author'], "modorganizer-installer_fomod", "installer_fomod", config['Main_Branch'], ["Qt5", "modorganizer-uibase","modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-installer_ncc", "installer_ncc", config['Main_Branch'], ["Qt5", "modorganizer-uibase", "ncc","modorganizer-game_features"], True),
    (config['Main_Author'], "modorganizer-bsa_extractor", "bsa_extractor", config['Main_Branch'], ["Qt5", "modorganizer-uibase", "modorganizer-bsatk"], True),
    (config['Main_Author'], "modorganizer-plugin_python", "plugin_python", config['Main_Branch'], ["Qt5", "boost", "Python",
                                                                                                   "modorganizer-uibase", "sip","modorganizer-game_features"], True),
    (config['Main_Author'], "githubpp", "githubpp", config['Main_Branch'], ["Qt5"], True),
    (config['Main_Author'], "modorganizer", "modorganizer", config['Main_Branch'], ["Qt5", "boost", "usvfs_32",
                                                                                    "modorganizer-uibase",
                                                                                    "modorganizer-archive",
                                                                                    "modorganizer-bsatk",
                                                                                    "modorganizer-esptk",
                                                                                    "modorganizer-game_features",
                                                                                    "usvfs", "githubpp",
                                                                                    "ncc", "openssl"], True),]:
    cmake_param = cmake_parameters() + ["-DCMAKE_INSTALL_PREFIX:PATH={}".format(config["paths"]["install"])]
    # build_step = cmake.CMake().arguments(cmake_param).install()

    # for dep in dependencies:
    #     build_step.depend(dep)

    project = Project(git_path)

    if Build:
        if config['Appveyor_Build']:
            jom_cmake_step = cmake.CMakeJOM().arguments(cmake_param).install()

            for dep in dependencies:
                jom_cmake_step.depend(dep)
            if os.getenv("APPVEYOR_PROJECT_NAME","") == git_path:
                project.depend(
                    jom_cmake_step.depend(
                        appveyor.SetProjectFolder(os.getenv("APPVEYOR_BUILD_FOLDER", ""))
                    )
                )
            else:
                project.depend(
                    jom_cmake_step.depend(
                        github.Source(author, git_path, branch, super_repository=tl_repo).set_destination(path)
                    )
                )
        else:
            vs_cmake_step = cmake.CMakeVS().arguments(cmake_param).install()

            for dep in dependencies:
                vs_cmake_step.depend(dep)

            vs_target = "Clean;Build" if config['rebuild'] else "Build"
            vs_msbuild_step = msbuild.MSBuild(os.path.join("vsbuild", "INSTALL.vcxproj"), None, None,
                                              "{}".format("x64" if config['architecture'] == 'x86_64' else "x86"),
                                              config['build_type'])

            project.depend(
                vs_msbuild_step.depend(
                    vs_cmake_step.depend(
                        github.Source(author, git_path, branch, super_repository=tl_repo).set_destination(path)
                    )
                )
            )
    else:
        project.depend(github.Source(author, git_path, branch, super_repository=tl_repo)
                       .set_destination(path))


def python_core_collect(context):
    ip = os.path.join(config["paths"]["install"], "bin")
    bp = python.python['build_path']

    try:
        shutil.rmtree(os.path.join(ip, "pythoncore"))
    except OSError:
        pass

    shutil.copytree(os.path.join(bp, "Lib"), os.path.join(ip, "pythoncore"), ignore=shutil.ignore_patterns("site-packages", '__pycache__'))

    path_segments = [bp, "PCbuild"]
    if config['architecture'] == "x86_64":
        path_segments.append("amd64")
    for f in glob(os.path.join(*path_segments,"*.pyd")):
        shutil.copy(f, os.path.join(ip, "pythoncore"))

    return True


Project("python_core") \
    .depend(build.Execute(python_core_collect)
            .depend("Python"))


if config['transifex_Enable']:
    from unibuild.projects import translations
    translationsBuild = Project("translationsBuild").depend("translations")


def copy_licenses(context):
    boost_version = config['boost_version']
    boost_tag_version = ".".join([_f for _f in [boost_version, config['boost_version_tag']] if _f])
    license_path = os.path.join(config["paths"]["install"], "bin", "licenses")
    build_path = config["paths"]["build"]
    try:
        os.makedirs(license_path)
    except:
        pass
    shutil.copy(os.path.join(config["paths"]["download"], "gpl-3.0.txt"), os.path.join(license_path, "GPL-v3.0.txt"))
    shutil.copy(os.path.join(config["paths"]["download"], "lgpl-3.0.txt"), os.path.join(license_path, "LGPL-v3.0.txt"))
    #shutil.copy(os.path.join(config["paths"]["download"], "BY-SA-v3.0.txt"), os.path.join(license_path, "BY-SA-v3.0.txt")) figure out a source, creative commons download doesn't work...
    shutil.copy(os.path.join(build_path, "usvfs", "udis86", "LICENSE"), os.path.join(license_path, "udis86.txt"))
    shutil.copy(os.path.join(build_path, "usvfs", "spdlog", "LICENSE"), os.path.join(license_path, "spdlog.txt"))
    shutil.copy(os.path.join(build_path, "usvfs", "fmt", "LICENSE.rst"), os.path.join(license_path, "fmt.txt"))
    if config['sip_dev_version']:
        sip_path = os.path.join(build_path, "sip-{}.dev{}".format(config['sip_version'], config['sip_dev_version']))
    else:
        sip_path = os.path.join(build_path, "sip-{}".format(config['sip_version']))
    if config['Appveyor_Build']:
        shutil.copy(os.path.join(build_path, "python-{}{}".format(config['python_version'], config['python_version_minor']),"Licenses","Sip", "LICENSE"), os.path.join(license_path, "sip.txt"))
        shutil.copy(os.path.join(build_path, "python-{}{}".format(config['python_version'], config['python_version_minor']),"Licenses","Sip", "LICENSE-GPL2"), os.path.join(license_path, "GPL-v2.0.txt"))
        shutil.copy(os.path.join(build_path, "python-{}{}".format(config['python_version'], config['python_version_minor']),"Licenses","Python","LICENSE"), os.path.join(license_path, "python.txt"))
    else:
        shutil.copy(os.path.join(sip_path, "LICENSE"), os.path.join(license_path, "sip.txt"))
        shutil.copy(os.path.join(sip_path, "LICENSE-GPL2"), os.path.join(license_path, "GPL-v2.0.txt"))
        shutil.copy(os.path.join(build_path, "python-{}{}".format(config['python_version'], config['python_version_minor']),"LICENSE"), os.path.join(license_path, "python.txt"))
    shutil.copy(os.path.join(build_path, "openssl-{}".format(config['openssl_version']), "LICENSE"), os.path.join(license_path, "openssl.txt"))
    shutil.copy(os.path.join(build_path, "modorganizer_super", "lootcli", "vsbuild", "src", "external", "src", "cpptoml", "LICENSE"), os.path.join(license_path, "cpptoml.txt"))
    shutil.copy(os.path.join(build_path, "boost_{}".format(boost_tag_version.replace(".", "_")), "LICENSE_1_0.txt"), os.path.join(license_path, "boost.txt"))
    shutil.copy(os.path.join(build_path, "7zip-{}".format(config['7zip_version']), "DOC", "License.txt"), os.path.join(license_path, "7zip.txt"))
    shutil.copy(os.path.join(build_path, "7zip-{}".format(config['7zip_version']), "DOC", "copying.txt"), os.path.join(license_path, "GNU-LGPL-v2.1.txt"))
    shutil.copy(os.path.join(build_path, "NexusClientCli", "NexusClientCLI", "Castle_License.txt"), os.path.join(license_path, "Castle.txt"))
    shutil.copy(os.path.join(build_path, "Nexus-Mod-Manager", "lib", "Antlr", "LICENSE.txt"), os.path.join(license_path, "AntlrBuildTask.txt"))
    shutil.copy(os.path.join(config["paths"]["download"], "LICENSE"), os.path.join(license_path, "DXTex.txt"))
    return True


Project("licenses") \
    .depend(build.Execute(copy_licenses)
        .depend(urldownload.URLDownload("https://www.gnu.org/licenses/lgpl-3.0.txt", 0))
        .depend(urldownload.URLDownload("https://www.gnu.org/licenses/gpl-3.0.txt", 0))
        .depend(urldownload.URLDownload("https://raw.githubusercontent.com/Microsoft/DirectXTex/master/LICENSE", 0).set_destination("DXTex.txt"))
        .depend("modorganizer"))


def copy_explorerpp(context):
    target_path = os.path.join(config["paths"]["install"], "bin", "explorer++")
    build_path = os.path.join(config["paths"]["build"], "explorer++")
    shutil.copytree(build_path, target_path)
    return True


Project("explorerpp") \
    .depend(build.Execute(copy_explorerpp)
        .depend(urldownload.URLDownload("https://ci.appveyor.com/api/projects/derceg/explorerplusplus/artifacts/explorer++_x64.zip?branch=master&job=Platform%3A%20x64", 0)
            .set_destination("explorer++")))


if config['Installer']:
    build_installer =  build.Run(r'"{}" {}'.format(config["paths"]["InnoSetup"],"dist/MO2-Installer.iss"),
              name="Build MO2 Installer")

    installer = Project("Installer") \
        .depend(build_installer
            .depend(github.Source(config['Main_Author'], "modorganizer-Installer", "Develop", super_repository=tl_repo)
                .set_destination("Installer")) \
                    .depend("modorganizer").depend("usvfs").depend("usvfs_32").depend("translationsBuild").depend("modorganizer-fnistool"))
