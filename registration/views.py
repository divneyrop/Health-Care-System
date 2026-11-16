from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import PatientRegistrationForm


def home(request):
    return render(request, 'home.html')


def register(request):

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                'Your account has been created successfully. You can now log in.'
            )

            return redirect('registration:login')

    else:
        form = PatientRegistrationForm()

    return render(
        request,
        'registration/registration.html',
        {'form': form}
    )
