from django.shortcuts import render
from django.http import JsonResponse
from userportal.common import account_or_staff
from userportal.common import Prometheus
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from ccldap.models import LdapAllocation
from ccldap.common import compute_allocations


@login_required
def index(request):
    context = {}
    username = request.META['username']
    context['compute_allocations'] = compute_allocations(username)
    context['default_allocations'] = []
    for alloc in LdapAllocation.objects.filter(members=username, status='active').all():
        if alloc.name.startswith('def-'):
            context['default_allocations'].append(alloc.name)
    return render(request, 'accountstats/index.html', context)


@login_required
@account_or_staff
def account(request, account):
    context = {}
    if account.endswith('_gpu'):
        context['gpu'] = True
    else:
        context['gpu'] = False
    return render(request, 'accountstats/account.html', context)


@login_required
@account_or_staff
def graph_cpu_allocated(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_alloc = 'count(slurm_job_core_usage_total{{account="{}", {}}}) by (user)'.format(account, prom.get_filter())
    stats_alloc = prom.query_prometheus_multiple(query_alloc, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_alloc:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_cpu_used(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_used = 'sum(rate(slurm_job_core_usage_total{{account="{}", {}}}[5m])) by (user)/ 1000000000'.format(account, prom.get_filter())
    stats_used = prom.query_prometheus_multiple(query_used, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_used:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_cpu_wasted(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_alloc = 'clamp_min(count(slurm_job_core_usage_total{{account="{}", {}}}) by (user) - sum(rate(slurm_job_core_usage_total{{account="{}", {}}}[5m])) by (user)/ 1000000000, 0)'.format(account, prom.get_filter(), account, prom.get_filter())
    stats_alloc = prom.query_prometheus_multiple(query_alloc, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_alloc:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_mem_allocated(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_alloc = 'sum(slurm_job_memory_limit{{account="{}", {}}}) by (user) /(1024*1024*1024)'.format(account, prom.get_filter())
    stats_alloc = prom.query_prometheus_multiple(query_alloc, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_alloc:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user
        })

    data['layout'] = {
        'yaxis': {
            'ticksuffix': 'GiB',
        }
    }

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_mem_used(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_used = 'sum(slurm_job_memory_max{{account="{}", {}}}) by (user) /(1024*1024*1024)'.format(account, prom.get_filter())
    stats_used = prom.query_prometheus_multiple(query_used, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_used:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user,
        })

    data['layout'] = {
        'yaxis': {
            'ticksuffix': 'GiB',
        }
    }

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_mem_wasted(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    query_alloc = 'clamp_min(sum(slurm_job_memory_limit{{account="{}", {}}}) by (user) - sum(slurm_job_memory_max{{account="{}", {}}}) by (user), 0) /(1024*1024*1024)'.format(account, prom.get_filter(), account, prom.get_filter())
    stats_alloc = prom.query_prometheus_multiple(query_alloc, datetime.now() - timedelta(hours=6), datetime.now())

    for line in stats_alloc:
        user = line['metric']['user']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': user
        })

    data['layout'] = {
        'yaxis': {
            'ticksuffix': 'GiB',
        }
    }

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_lustre_mdt(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'sum(rate(lustre_job_stats_total{{component=~"mdt",account=~"{}", {}}}[5m])) by (user, fs) !=0'.format(account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())
    data = {'lines': []}
    for line in stats:
        user = line['metric']['user']
        fs = line['metric']['fs']
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': '{} {}'.format(user, fs)
        })

    data['layout'] = {
        'yaxis': {
            'ticksuffix': ' IOPS'
        }
    }
    return JsonResponse(data)


@login_required
@account_or_staff
def graph_lustre_ost(request, account):
    prom = Prometheus(settings.PROMETHEUS)
    data = {'lines': []}
    for i in ['read', 'write']:
        query = '(sum(rate(lustre_job_{}_bytes_total{{component=~"ost",account=~"{}",target=~".*-OST.*", {}}}[5m])) by (user, fs)) / (1024*1024)'.format(i, account, prom.get_filter())
        stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

        for line in stats:
            fs = line['metric']['fs']
            user = line['metric']['user']
            x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
            y = line['y']
            data['lines'].append({
                'x': x,
                'y': y,
                'type': 'scatter',
                'name': '{} {} {}'.format(i, fs, user)
            })

    data['layout'] = {
        'yaxis': {
            'ticksuffix': ' MiB/s'
        }
    }
    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_allocated(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'count(slurm_job_utilization_gpu{{account="{}", {}}}) by (user)'.format(account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_used(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'sum(slurm_job_utilization_gpu{{account="{}", {}}}) by (user) / 100'.format(account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_wasted(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'count(slurm_job_utilization_gpu{{account="{}", {}}}) by (user) - sum(slurm_job_utilization_gpu{{account="{}", {}}}) by (user) / 100'.format(account, prom.get_filter(), account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_power_allocated(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'count(slurm_job_power_gpu{{account="{}", {}}}) by (user) * 300'.format(account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })
    data['layout'] = {
        'yaxis': {
            'ticksuffix': ' W',
        }
    }

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_power_used(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = 'sum(slurm_job_power_gpu{{account="{}", {}}}) by (user) / 1000'.format(account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })
    data['layout'] = {
        'yaxis': {
            'ticksuffix': ' W',
        }
    }

    return JsonResponse(data)


@login_required
@account_or_staff
def graph_gpu_power_wasted(request, account):
    prom = Prometheus(settings.PROMETHEUS)

    query = '(count(slurm_job_power_gpu{{account="{}", {}}}) by (user) * 300) - (sum(slurm_job_power_gpu{{account="{}", {}}}) by (user) / 1000)'.format(account, prom.get_filter(), account, prom.get_filter())
    stats = prom.query_prometheus_multiple(query, datetime.now() - timedelta(hours=6), datetime.now())

    data = {'lines': []}
    for line in stats:
        x = list(map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'), line['x']))
        y = line['y']
        data['lines'].append({
            'x': x,
            'y': y,
            'type': 'scatter',
            'stackgroup': 'one',
            'name': line['metric']['user']
        })
    data['layout'] = {
        'yaxis': {
            'ticksuffix': ' W',
        }
    }

    return JsonResponse(data)
