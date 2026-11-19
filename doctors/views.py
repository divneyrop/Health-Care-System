from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    if request.user.role != 'DOCTOR':
        messages.info(request, 'The doctor dashboard is available to doctor accounts.')
        return redirect('registration:home')

    return render(request, 'doctors/dashboard.html')
