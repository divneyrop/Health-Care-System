from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    if request.user.role != 'PATIENT':
        messages.info(request, 'The patient dashboard is available to patient accounts.')
        return redirect('registration:home')

    return render(request, 'patients/dashboard.html')
