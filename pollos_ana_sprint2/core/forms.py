from django import forms
from .models import Producto,Categoria
class ProductoForm(forms.ModelForm):
 class Meta:
  model=Producto
  fields=['nombre','categoria','precio','imagen','activo']
  widgets={'nombre':forms.TextInput(attrs={'class':'form-control'}),'categoria':forms.Select(attrs={'class':'form-select'}),'precio':forms.NumberInput(attrs={'class':'form-control','min':'0.01','step':'0.01'}),'imagen':forms.ClearableFileInput(attrs={'class':'form-control'}),'activo':forms.CheckboxInput(attrs={'class':'form-check-input'})}
class CategoriaForm(forms.ModelForm):
 class Meta:
  model=Categoria
  fields=['nombre']
  widgets={'nombre':forms.TextInput(attrs={'class':'form-control'})}
