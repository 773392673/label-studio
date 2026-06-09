"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import os

from core.feature_flags import all_flags
from core.utils.common import collect_versions
from django.conf import settings as django_settings


def _is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv')
        or os.path.isfile(path)
        and any('docker' in line for line in open(path, encoding='utf-8'))
    )


def sentry_fe(request):
    # return the value you want as a dictionary, you may add multiple values in there
    return {'SENTRY_FE': django_settings.SENTRY_FE}


def settings(request):
    """Make available django settings on each template page"""
    versions = collect_versions()

    os_release = versions.get('label-studio-os-backend', {}).get('commit', 'none')[0:6]
    # django templates can't access names with hyphens
    versions['lsf'] = versions.get('label-studio-frontend', {})
    versions['lsf']['commit'] = versions['lsf'].get('commit', os_release)[0:6]

    versions['dm2'] = versions.get('dm2', {})
    versions['dm2']['commit'] = versions['dm2'].get('commit', os_release)[0:6]

    versions['backend'] = {}
    if 'label-studio-os-backend' in versions:
        versions['backend']['commit'] = versions['label-studio-os-backend'].get('commit', 'none')[0:6]
    if 'label-studio-enterprise-backend' in versions:
        versions['backend']['commit'] = versions['label-studio-enterprise-backend'].get('commit', 'none')[0:6]

    feature_flags = {}
    if hasattr(request, 'user'):
        feature_flags = all_flags(request.user)

    deployment_info = {
        'mode': 'Docker' if _is_docker() else 'Local',
        'version': versions.get('release', 'unknown'),
        'access_url': django_settings.HOSTNAME or (request.get_host() if hasattr(request, 'get_host') else ''),
    }

    return {'settings': django_settings, 'versions': versions, 'feature_flags': feature_flags, 'deployment_info': deployment_info}
