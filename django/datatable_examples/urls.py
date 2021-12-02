from django.urls import path
from django.views.generic.base import RedirectView
import datatable_examples.views.main as main_views
import datatable_examples.views.aggregations as aggregations_views
import datatable_examples.views.horizontal as horizontal_views
import datatable_examples.views.widgets as widgets_views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='example1', )),
    path('datatable-redirect/', RedirectView.as_view(pattern_name='example1', ), name='django-filtered-datatables'),
    path('<int:pk>', main_views.CompanyView.as_view(), name='company'),
    path('example-1', main_views.Example1.as_view(), name='example1'),
    path('example-2/<int:pk>/', main_views.Example2.as_view(), name='example2'),
    path('example-2/', main_views.Example2.as_view(), name='example2'),
    path('example-3', main_views.Example3.as_view(), name='example3'),
    path('example-4', main_views.Example4.as_view(), name='example4'),
    path('example-5', main_views.Example5.as_view(), name='example5'),
    path('example-6', main_views.Example6.as_view(), name='example6'),
    path('example-7', main_views.Example7.as_view(), name='example7'),
    path('example-8', main_views.Example8.as_view(), name='example8'),
    path('example-9', main_views.Example9.as_view(), name='example9'),
    path('example-10', main_views.Example10.as_view(), name='example10'),
    path('example-11', main_views.Example11.as_view(), name='example11'),
    path('example-12', main_views.Example12.as_view(), name='example12'),
    path('example-13', main_views.Example13.as_view(), name='example13'),

    path('orderable', main_views.ExampleReorder.as_view(), name='reorder'),

    path('widget', widgets_views.WidgetView.as_view(), name='widget'),

    path('aggregations/standard', aggregations_views.ExampleAggregations.as_view(), name='aggregations'),
    path('aggregation/horizontal', aggregations_views.ExampleAggregationsHorizontal.as_view(),
         name='aggregations_horizontal'),

    path('horizontal', horizontal_views.ExampleHorizontal.as_view(),
         name='horizontal'),


]
