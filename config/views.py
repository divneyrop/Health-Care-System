from django.shortcuts import render


def csrf_failure(request, reason=''):
    return render(request, 'errors/csrf_failure.html', status=403)
