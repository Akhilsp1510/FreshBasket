from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomerRegistrationForm, CustomerLoginForm, ProfileUpdateForm, AddressForm
from .models import Address


def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to FreshBasket, {user.first_name}! Your account has been created.')
            return redirect('products:home')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create Account'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')
    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '/')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = CustomerLoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Sign In'})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been signed out. See you soon!')
    return redirect('products:home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    addresses = request.user.addresses.all()
    return render(request, 'accounts/profile.html', {
        'form': form,
        'addresses': addresses,
        'title': 'My Profile'
    })


@login_required
def add_address_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.filter(is_default=True).update(is_default=False)
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('accounts:profile')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def edit_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.cleaned_data.get('is_default'):
                request.user.addresses.filter(is_default=True).update(is_default=False)
            form.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('accounts:profile')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})


@login_required
def delete_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address removed.')
    return redirect('accounts:profile')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'title': 'Change Password'
    })
