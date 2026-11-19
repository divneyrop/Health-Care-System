from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    if request.user.role != 'STAFF':
        messages.info(request, 'The hospital staff dashboard is available to staff accounts.')
        return redirect('registration:home')

    return render(request, 'hospital_staff/dashboard.html')
