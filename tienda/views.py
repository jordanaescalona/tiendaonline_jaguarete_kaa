from django.shortcuts import render
#autenticacion
from django.contrib.auth import authenticate
from django.contrib.auth import login
#desloguearse
from django.contrib.auth import logout
#mensajes
from django.contrib import messages
#redireccionar
from django.shortcuts import redirect
#importo formulario
from .forms import RegisterForm,ProductoForm
#importo el modelo User incorporado 
from django.contrib.auth.models import User
#importamos los modelos
from .models import *
#importamos error 404
from django.shortcuts import get_object_or_404
#importamos ListView
from django.views.generic.list import ListView
#libreria login requerido
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect

from cart.cart import Cart

# Create your views here.
def index(request):
    
    tresProductos = Producto.objects.all().order_by('-id')[:3]
    restoProductos = Producto.objects.all().order_by('-id')[3:10]
    categorias = Categoria.objects.all()
    return render(request,'index.html',{
        'title':'Index',
        'tresProductos':tresProductos,
        'restoProductos':restoProductos,
        'categorias':categorias
    })

def acerca(request):
    categorias = Categoria.objects.all()
    return render(request,'acerca.html',{
        'title':'Acerca de',
        'categorias':categorias
    })

def login_view(request):
    
    if not request.user.is_authenticated: 
        categorias = Categoria.objects.all()
        
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(username=username,password=password)

            if user:
                login(request,user)
                #mensaje de exito
                messages.success(request,'Bienvenido {}'.format(user.username))
                return redirect('tienda:index')
            else:
                #mensaje de error
                messages.error(request, 'Usuario o contaseña no validos')

        return render(request,'tienda/users/login.html',{
            'categorias':categorias
        })
    return redirect('tienda:index')

def logout_view(request):
    if request.user.is_authenticated: 
        logout(request)
        messages.success(request,'Sesión cerrada correctamente')
        return redirect('tienda:index')

    return redirect('tienda:index')

def register(request):
    categorias = Categoria.objects.all()
    #si el usuario ya esta autenticado lo enviamos a index
    if request.user.is_authenticated:
        return redirect('tienda:index')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
         
        #utilizamos la funcion que creamos en forms.py para registrar un nuevo usuario
        user = form.save()
        if user:
            login(request,user)
            messages.success(request,'Usuario creado exitosamente!')
            return redirect('tienda:index')
        
    return render(request,'tienda/users/register.html',{
        'form':form,
        'categorias':categorias
    })

def ver_producto(request,producto_id):
    
    producto = get_object_or_404(Producto,id=producto_id)
    categorias = Categoria.objects.all()

    #realizamos una validacion
    # queremos sabes si estamos pasando una variable cantidad al formulario
    if request.method == 'GET' and request.GET.get('cantidad'):
        #En este caso Cart es request porque es un objeto 
        cart = Cart(request)
        cart.add(producto,int(request.GET.get('cantidad')))

        messages.success(request,'Producto agregado exitosamente al carrito!')
        return redirect('tienda:index')


    return render(request,'productos/ver_producto.html',{
        'producto':producto,
        'categorias': categorias,
    })

def producto_categoria(request,categoria_id):
    categoria = Categoria.objects.get(pk=categoria_id)
    categorias = Categoria.objects.all()
    productos = Producto.objects.all().filter(categoria=categoria)
    titulo = categoria.descripcion
    
    return render(request,'productos/categoria.html',{
        'categoria':categoria,
        'categorias':categorias,
        'productos': productos,
        'titulo':titulo
    })

class BuscarProductoListView(ListView):
    template_name = 'productos/buscar.html'
    
    #capturamos el valor del input del formulario
    def query(self):
        return self.request.GET.get('q')

    #El metodo get_queryset nos permite retornar la consulta
    def get_queryset(self):
        return Producto.objects.filter(descripcion__icontains=self.query())
    
    #Para poder ingresar a los datos a buscar el resultado hago uso de get_context_data
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.query()
        context['count'] = context['producto_list'].count()
        context['categorias'] = Categoria.objects.all() 
        return context

@login_required(login_url='login')
def cargar_producto(request):
    
    if request.user.is_staff: 
        categorias = Categoria.objects.all()

        form = ProductoForm(request.POST, request.FILES)
        
        if request.method == 'POST' and form.is_valid():
        
            producto = form.save()
            if producto:
                messages.success(request,'Producto cargado exitosamente!')
                return redirect('tienda:nuevo')
            
        return render(request,'productos/nuevo_producto.html',{
            'form':form,
            'categorias':categorias
        })
    return redirect('tienda:index')

@login_required(login_url='login')
def editar_producto(request,producto_id):

    if request.user.is_staff:
        un_producto = get_object_or_404(Producto,id=producto_id)
        categorias = Categoria.objects.all()
        if request.method == 'POST':
            form = ProductoForm(data=request.POST,files=request.FILES,instance=un_producto)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(request.GET['next'])
        else:
            form = ProductoForm(instance=un_producto)
            return render(request,'productos/modificar_producto.html',{
                'producto':un_producto,
                'form': form,
                'categorias':categorias
                
            })
    return redirect('tienda:index')

@login_required(login_url='login')
def eliminar_producto(request,producto_id):
    if request.user.is_staff:
        un_producto = get_object_or_404(Producto,id=producto_id)
        un_producto.delete()
    messages.success(request,'Producto eliminado exitosamente!')
    return redirect('tienda:index')    


#--------------Carrito
@login_required(login_url='tienda:login')
def cart_detalle(request):
    categorias = Categoria.objects.all()
    return render(request,'cart/detail.html',{
        'cart':Cart(request),
        'categorias':categorias
    })

#eliminar productos del carrito
def cart_remove(request,pk):
    cart = Cart(request)
    producto = get_object_or_404(Producto,pk=pk)

    cart.remove(producto)

    return redirect('tienda:cart_detalle')

#eliminar carrito
def cart_delete(request):
    cart = Cart(request)
    cart.clear()
    messages.success(request,'Carrito vaciado exitosamente!')
    return redirect('tienda:index')