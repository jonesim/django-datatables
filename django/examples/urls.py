from django.urls import path
import examples.views as views

urlpatterns = [
    path('', views.Example1.as_view()),
    path('<int:pk>', views.CompanyView.as_view(), name='company'),
    path('example-1', views.Example1.as_view(), name='example1'),
    path('example-2/<int:pk>/', views.Example2.as_view(), name='example2'),
    path('example-2/', views.Example2.as_view(), name='example2'),
    path('example-3', views.Example3.as_view(), name='example3'),
    path('example-4', views.Example4.as_view(), name='example4'),
    path('example-5', views.Example5.as_view(), name='example5'),
    path('example-6', views.Example6.as_view(), name='example6'),
    path('example-7', views.Example7.as_view(), name='example7'),
    path('example-8', views.Example8.as_view(), name='example8'),
    path('example-9', views.Example9.as_view(), name='example9'),
    path('example-10', views.Example10.as_view(), name='example10'),
    path('example-11', views.Example11.as_view(), name='example11'),
    path('example-12', views.Example12.as_view(), name='example12'),
    path('example-13', views.Example13.as_view(), name='example13'),
]
