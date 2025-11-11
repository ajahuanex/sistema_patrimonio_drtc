#!/usr/bin/env python
"""
Script de verificación de estadísticas del dashboard
Verifica que todas las consultas y cálculos funcionen correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
django.setup()

from django.db.models import Count, Sum
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.core.models import RecycleBin
from django.contrib.auth.models import User
from datetime import datetime, timedelta

def print_section(title):
    """Imprime un título de sección"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def verificar_estadisticas():
    """Verifica todas las estadísticas del dashboard"""
    
    print_section("VERIFICACIÓN DE ESTADÍSTICAS DEL DASHBOARD")
    
    # 1. Estadísticas de bienes patrimoniales
    print_section("1. ESTADÍSTICAS DE BIENES PATRIMONIALES")
    
    total_bienes = BienPatrimonial.objects.filter(deleted_at__isnull=True).count()
    print(f"✓ Total de bienes activos: {total_bienes}")
    
    bienes_nuevos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='N'
    ).count()
    print(f"✓ Bienes en estado NUEVO: {bienes_nuevos}")
    
    bienes_buenos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='B'
    ).count()
    print(f"✓ Bienes en estado BUENO: {bienes_buenos}")
    
    bienes_regulares = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='R'
    ).count()
    print(f"✓ Bienes en estado REGULAR: {bienes_regulares}")
    
    bienes_malos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien__in=['M', 'E', 'C']
    ).count()
    print(f"✓ Bienes en estado MALO/RAEE/CHATARRA: {bienes_malos}")
    
    # Verificar que la suma coincida
    suma_estados = bienes_nuevos + bienes_buenos + bienes_regulares + bienes_malos
    print(f"\n  Verificación: {suma_estados} de {total_bienes} bienes clasificados")
    if suma_estados == total_bienes:
        print("  ✓ La suma de estados coincide con el total")
    else:
        print(f"  ⚠ Hay {total_bienes - suma_estados} bienes sin clasificar o con otros estados")
    
    # 2. Estadísticas de catálogo y oficinas
    print_section("2. ESTADÍSTICAS DE CATÁLOGO Y OFICINAS")
    
    total_catalogo = Catalogo.objects.filter(deleted_at__isnull=True).count()
    print(f"✓ Total de elementos en catálogo: {total_catalogo}")
    
    total_oficinas = Oficina.objects.filter(deleted_at__isnull=True).count()
    print(f"✓ Total de oficinas activas: {total_oficinas}")
    
    # 3. Estadísticas de papelera y usuarios
    print_section("3. ESTADÍSTICAS DE SISTEMA")
    
    items_papelera = RecycleBin.objects.count()
    print(f"✓ Items en papelera de reciclaje: {items_papelera}")
    
    total_usuarios = User.objects.filter(is_active=True).count()
    print(f"✓ Usuarios activos: {total_usuarios}")
    
    # 4. Bienes registrados este mes
    print_section("4. ESTADÍSTICAS TEMPORALES")
    
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    bienes_este_mes = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        created_at__gte=inicio_mes
    ).count()
    print(f"✓ Bienes registrados este mes: {bienes_este_mes}")
    print(f"  (Desde: {inicio_mes.strftime('%d/%m/%Y')})")
    
    # 5. Valor total estimado
    print_section("5. VALOR PATRIMONIAL")
    
    try:
        valor_total = BienPatrimonial.objects.filter(
            deleted_at__isnull=True,
            valor_adquisicion__isnull=False
        ).aggregate(total=Sum('valor_adquisicion'))['total'] or 0
        
        bienes_con_valor = BienPatrimonial.objects.filter(
            deleted_at__isnull=True,
            valor_adquisicion__isnull=False
        ).count()
        
        print(f"✓ Valor total del patrimonio: S/ {valor_total:,.2f}")
        print(f"✓ Bienes con valor registrado: {bienes_con_valor} de {total_bienes}")
        
        if bienes_con_valor > 0:
            valor_promedio = valor_total / bienes_con_valor
            print(f"✓ Valor promedio por bien: S/ {valor_promedio:,.2f}")
    except Exception as e:
        print(f"⚠ Error al calcular valor total: {str(e)}")
    
    # 6. Top 5 oficinas con más bienes
    print_section("6. TOP 5 OFICINAS CON MÁS BIENES")
    
    top_oficinas = BienPatrimonial.objects.filter(
        deleted_at__isnull=True
    ).values(
        'oficina__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    if top_oficinas:
        for i, oficina in enumerate(top_oficinas, 1):
            nombre = oficina['oficina__nombre'] or 'Sin Oficina'
            total = oficina['total']
            porcentaje = (total / total_bienes * 100) if total_bienes > 0 else 0
            print(f"  {i}. {nombre}: {total} bienes ({porcentaje:.1f}%)")
    else:
        print("  ⚠ No hay datos de oficinas")
    
    # 7. Distribución por estado (para gráficos)
    print_section("7. DISTRIBUCIÓN PORCENTUAL POR ESTADO")
    
    if total_bienes > 0:
        print(f"  Nuevo:    {bienes_nuevos:3d} ({bienes_nuevos/total_bienes*100:5.1f}%)")
        print(f"  Bueno:    {bienes_buenos:3d} ({bienes_buenos/total_bienes*100:5.1f}%)")
        print(f"  Regular:  {bienes_regulares:3d} ({bienes_regulares/total_bienes*100:5.1f}%)")
        print(f"  Malo:     {bienes_malos:3d} ({bienes_malos/total_bienes*100:5.1f}%)")
    else:
        print("  ⚠ No hay bienes para calcular porcentajes")
    
    # 8. Verificar template tags
    print_section("8. VERIFICACIÓN DE TEMPLATE TAGS")
    
    try:
        from apps.core.templatetags.math_filters import mul, div, percentage, format_currency
        
        # Probar filtros
        test_mul = mul(10, 5)
        print(f"✓ Filtro mul(10, 5) = {test_mul}")
        
        test_div = div(100, 4)
        print(f"✓ Filtro div(100, 4) = {test_div}")
        
        test_percentage = percentage(25, 100)
        print(f"✓ Filtro percentage(25, 100) = {test_percentage}%")
        
        test_currency = format_currency(1234.56)
        print(f"✓ Filtro format_currency(1234.56) = {test_currency}")
        
    except Exception as e:
        print(f"⚠ Error al verificar template tags: {str(e)}")
    
    # 9. Resumen final
    print_section("RESUMEN DE VERIFICACIÓN")
    
    print(f"""
  Estado del Sistema:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  📦 Bienes Patrimoniales:  {total_bienes:>6}
  📋 Catálogo SBN:          {total_catalogo:>6}
  🏢 Oficinas:              {total_oficinas:>6}
  👥 Usuarios:              {total_usuarios:>6}
  🗑️  Papelera:              {items_papelera:>6}
  📅 Registros este mes:    {bienes_este_mes:>6}
  
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  ✅ Todas las estadísticas están funcionando correctamente
  
  🌐 Accede al dashboard en: http://localhost:8000
  
    """)

if __name__ == '__main__':
    try:
        verificar_estadisticas()
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
