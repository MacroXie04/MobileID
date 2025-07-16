from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.forms import ModelForm
from django import forms
from mobileid.models import UserAccount, Barcode, UserBarcodeSettings
from django.contrib.auth.models import User
import uuid


class BarcodeForm(ModelForm):
    class Meta:
        model = Barcode
        fields = ['barcode_type', 'barcode']
        widgets = {
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter barcode value'
            }),
            'barcode_type': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            user_account = UserAccount.objects.get(user=user)
            if user_account.account_type == 'User':
                # User类型只能添加Others类型的条码
                self.fields['barcode_type'].choices = [
                    ('Others', 'Others')
                ]
                self.fields['barcode_type'].initial = 'Others'
            elif user_account.account_type == 'School':
                # School类型可以添加Others和DynamicBarcode
                self.fields['barcode_type'].choices = [
                    ('Others', 'Others'),
                    ('DynamicBarcode', 'DynamicBarcode')
                ]


class UserBarcodeSettingsForm(ModelForm):
    class Meta:
        model = UserBarcodeSettings
        fields = ['barcode', 'server_verification', 'timestamp_verification', 'barcode_pull']
        widgets = {
            'barcode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'server_verification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'timestamp_verification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'barcode_pull': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            user_account = UserAccount.objects.get(user=user)

            # 设置可选择的条码（用户自己创建的条码）
            user_barcodes = Barcode.objects.filter(user=user)
            self.fields['barcode'].queryset = user_barcodes
            self.fields['barcode'].empty_label = "Select a barcode"

            if user_account.account_type == 'User':
                # User类型只能选择条码，其他设置不可见
                self.fields['server_verification'].widget = forms.HiddenInput()
                self.fields['timestamp_verification'].widget = forms.HiddenInput()
                self.fields['barcode_pull'].widget = forms.HiddenInput()


@login_required(login_url='/login/')
def manage_barcode(request):
    try:
        user_account = UserAccount.objects.get(user=request.user)
    except UserAccount.DoesNotExist:
        messages.error(request, "User account not found.")
        return redirect('home')

    # 获取或创建用户的条码设置
    user_barcode_settings, created = UserBarcodeSettings.objects.get_or_create(
        user=request.user
    )

    # 获取用户的条码列表
    user_barcodes = Barcode.objects.filter(user=request.user)

    # 处理添加条码的表单
    if request.method == 'POST':
        if 'add_barcode' in request.POST:
            barcode_form = BarcodeForm(request.POST, user=request.user)
            if barcode_form.is_valid():
                try:
                    barcode = barcode_form.save(commit=False)
                    barcode.user = request.user
                    barcode.save()
                    messages.success(request, "Barcode added successfully!")
                    return redirect('manage_barcode')
                except Exception as e:
                    messages.error(request, f"Error adding barcode: {str(e)}")
            else:
                messages.error(request, "Please correct the errors in the barcode form.")

        elif 'update_settings' in request.POST:
            settings_form = UserBarcodeSettingsForm(
                request.POST,
                instance=user_barcode_settings,
                user=request.user
            )
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, "Barcode settings updated successfully!")
                return redirect('mobileid:web_barcode_settings')
            else:
                messages.error(request, "Please correct the errors in the settings form.")

    # 创建表单实例
    barcode_form = BarcodeForm(user=request.user)
    settings_form = UserBarcodeSettingsForm(
        instance=user_barcode_settings,
        user=request.user
    )

    context = {
        'user_account': user_account,
        'user_barcodes': user_barcodes,
        'barcode_form': barcode_form,
        'settings_form': settings_form,
        'user_barcode_settings': user_barcode_settings,
    }

    return render(request, 'manage/manage_barcode.html', context)


@login_required
def delete_barcode(request, barcode_id):
    """删除条码的视图"""
    if request.method == 'POST':
        try:
            barcode = get_object_or_404(Barcode, id=barcode_id, user=request.user)

            # 检查是否有用户设置引用这个条码
            if UserBarcodeSettings.objects.filter(barcode=barcode).exists():
                messages.warning(request, "Cannot delete barcode as it is currently in use in settings.")
            else:
                barcode.delete()
                messages.success(request, "Barcode deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting barcode: {str(e)}")

    return redirect('mobileid:web_manage_barcode')


@login_required
def get_barcode_info(request, barcode_id):
    """获取条码信息的AJAX视图"""
    try:
        barcode = get_object_or_404(Barcode, id=barcode_id, user=request.user)
        data = {
            'barcode_value': barcode.barcode,
            'barcode_type': barcode.barcode_type,
            'time_created': barcode.time_created.strftime('%Y-%m-%d %H:%M:%S') if barcode.time_created else '',
            'barcode_uuid': str(barcode.barcode_uuid)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)