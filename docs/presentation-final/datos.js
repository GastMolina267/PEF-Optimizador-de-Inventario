/* ==========================================================================
   DATOS REALES DE LA DEMO — Proyecto Final PEF
   Generados sobre data/datasets/demo_oral.json (30 productos) con el modelo
   reentrenado igual que benchmarks/comparar_ia.py (seed=42, 20 períodos,
   25 pedidos por período). Cada fila:
     fv   = los 10 datos de FeatureVector (src/ia/tipos.py), en orden
     conv = [demanda, P(quiebre), riesgo, alerta]   estrategia CONVENCIONAL
     ia   = [demanda, P(quiebre), riesgo, alerta]   estrategia IA
     hib  = [demanda, P(quiebre), riesgo, alerta, ruta]  estrategia HIBRIDA
   No editar a mano: si cambia el modelo, regenerar y revisar las láminas.
   ========================================================================== */
window.PEF4_DATOS = {
  productos: [
    {"id":1,"n":"Taladro Percutor 750W","cat":"Ferretería y Herramientas","stock":15,"fv":[1.0,1.0,1.0,0.0,15,45000.0,7.5,0.0,1.0,15.0],"conv":[1.0,0.047,"bajo",false],"ia":[13.7,0.434,"medio",false],"hib":[1.0,0.047,"bajo",false,"rapido"]},
    {"id":2,"n":"Amoladora Angular 115mm","cat":"Ferretería y Herramientas","stock":10,"fv":[0.0,0.0,0.0,0.0,10,38000.0,10.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[14.5,0.475,"medio",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":3,"n":"Juego de Destornilladores x6","cat":"Ferretería y Herramientas","stock":25,"fv":[0.0,0.0,0.0,0.0,25,12000.0,25.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[8.4,0.127,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":4,"n":"Martillo Galponero 500g","cat":"Ferretería y Herramientas","stock":30,"fv":[2.0,1.0,2.0,0.0,30,9500.0,10.0,0.0,1.0,15.0],"conv":[2.0,0.039,"bajo",false],"ia":[5.3,0.062,"bajo",false],"hib":[2.0,0.039,"bajo",false,"rapido"]},
    {"id":5,"n":"Sierra Caladora 600W","cat":"Ferretería y Herramientas","stock":0,"fv":[1.0,1.0,1.0,0.0,0,32000.0,0.0,1.0,1.0,0.0],"conv":[1.0,1.0,"critico",true],"ia":[12.0,0.915,"critico",true],"hib":[12.0,0.915,"critico",true,"ia"]},
    {"id":6,"n":"Cable Unipolar 2.5mm 100m","cat":"Electricidad e Iluminación","stock":40,"fv":[1.0,1.0,1.0,0.0,40,28000.0,20.0,0.0,1.0,40.0],"conv":[1.0,0.018,"bajo",false],"ia":[9.8,0.095,"bajo",false],"hib":[1.0,0.018,"bajo",false,"rapido"]},
    {"id":7,"n":"Foco LED 12W Luz Fría","cat":"Electricidad e Iluminación","stock":120,"fv":[30.0,2.0,15.0,25.0,120,1800.0,3.87,0.0,2.0,8.0],"conv":[30.0,0.096,"bajo",false],"ia":[6.8,0.0,"bajo",false],"hib":[30.0,0.096,"bajo",false,"rapido"]},
    {"id":8,"n":"Foco LED 9W Luz Cálida","cat":"Electricidad e Iluminación","stock":80,"fv":[5.0,1.0,5.0,0.0,80,1500.0,13.33,0.0,1.0,16.0],"conv":[5.0,0.032,"bajo",false],"ia":[3.0,0.002,"bajo",false],"hib":[5.0,0.032,"bajo",false,"rapido"]},
    {"id":9,"n":"Disyuntor Diferencial 25A","cat":"Electricidad e Iluminación","stock":20,"fv":[0.0,0.0,0.0,0.0,20,31000.0,20.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[12.8,0.295,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":10,"n":"Llave Térmica Bipolar 16A","cat":"Electricidad e Iluminación","stock":0,"fv":[2.0,1.0,2.0,0.0,0,8500.0,0.0,1.0,1.0,0.0],"conv":[2.0,1.0,"critico",true],"ia":[6.4,0.775,"critico",true],"hib":[6.4,0.775,"critico",true,"ia"]},
    {"id":11,"n":"Pintura Látex Interior 20L","cat":"Pinturas y Adhesivos","stock":18,"fv":[2.0,1.0,2.0,0.0,18,52000.0,6.0,0.0,1.0,9.0],"conv":[2.0,0.063,"bajo",false],"ia":[15.0,0.435,"medio",false],"hib":[2.0,0.063,"bajo",false,"rapido"]},
    {"id":12,"n":"Pintura Látex Interior 10L","cat":"Pinturas y Adhesivos","stock":22,"fv":[0.0,0.0,0.0,0.0,22,29000.0,22.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[12.3,0.259,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":13,"n":"Pintura Látex Interior 4L","cat":"Pinturas y Adhesivos","stock":35,"fv":[0.0,0.0,0.0,0.0,35,14000.0,35.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[8.8,0.09,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":14,"n":"Esmalte Sintético Brillante 1L","cat":"Pinturas y Adhesivos","stock":25,"fv":[0.0,0.0,0.0,0.0,25,8900.0,25.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[7.7,0.113,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":15,"n":"Rodillo Antigoteo 22cm","cat":"Pinturas y Adhesivos","stock":50,"fv":[3.0,1.0,3.0,0.0,50,4500.0,12.5,0.0,1.0,16.67],"conv":[3.0,0.032,"bajo",false],"ia":[4.0,0.016,"bajo",false],"hib":[3.0,0.032,"bajo",false,"rapido"]},
    {"id":16,"n":"Pincel N°20 Cerda Blanca","cat":"Pinturas y Adhesivos","stock":60,"fv":[2.0,1.0,2.0,0.0,60,2200.0,20.0,0.0,1.0,30.0],"conv":[2.0,0.02,"bajo",false],"ia":[3.8,0.01,"bajo",false],"hib":[2.0,0.02,"bajo",false,"rapido"]},
    {"id":17,"n":"Caño PVC 110mm x 4m","cat":"Plomería y Grifería","stock":15,"fv":[0.0,0.0,0.0,0.0,15,16500.0,15.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[9.6,0.22,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":18,"n":"Codo PVC 110mm a 90°","cat":"Plomería y Grifería","stock":45,"fv":[4.0,1.0,4.0,0.0,45,2800.0,9.0,0.0,1.0,11.25],"conv":[4.0,0.046,"bajo",false],"ia":[3.3,0.017,"bajo",false],"hib":[4.0,0.046,"bajo",false,"rapido"]},
    {"id":19,"n":"Adhesivo para PVC 250cc","cat":"Plomería y Grifería","stock":30,"fv":[0.0,0.0,0.0,0.0,30,5100.0,30.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[6.8,0.079,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":20,"n":"Canilla Monocomando Cocina","cat":"Plomería y Grifería","stock":12,"fv":[0.0,0.0,0.0,0.0,12,42000.0,12.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[15.4,0.494,"medio",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":21,"n":"Flexible Mallado 1/2 x 40cm","cat":"Plomería y Grifería","stock":2,"fv":[5.0,1.0,5.0,0.0,2,3400.0,0.33,1.0,1.0,0.4],"conv":[5.0,0.85,"critico",true],"ia":[4.2,0.63,"medio",true],"hib":[4.2,0.63,"medio",true,"ia"]},
    {"id":22,"n":"Tornillo Autoperforante 10x1 (x100)","cat":"Bulonería y Tornillería","stock":100,"fv":[15.0,2.0,7.5,6.25,100,3200.0,6.25,0.0,2.0,13.33],"conv":[15.0,0.059,"bajo",false],"ia":[4.5,0.001,"bajo",false],"hib":[15.0,0.059,"bajo",false,"rapido"]},
    {"id":23,"n":"Tornillo Autoperforante 10x2 (x100)","cat":"Bulonería y Tornillería","stock":90,"fv":[5.0,1.0,5.0,0.0,90,4100.0,15.0,0.0,1.0,18.0],"conv":[5.0,0.028,"bajo",false],"ia":[3.6,0.001,"bajo",false],"hib":[5.0,0.028,"bajo",false,"rapido"]},
    {"id":24,"n":"Tarugo con Tope N°8 (x100)","cat":"Bulonería y Tornillería","stock":150,"fv":[4.0,1.0,4.0,0.0,150,2100.0,30.0,0.0,1.0,37.5],"conv":[4.0,0.014,"bajo",false],"ia":[3.8,0.0,"bajo",false],"hib":[4.0,0.014,"bajo",false,"rapido"]},
    {"id":25,"n":"Tuerca Hexagonal 1/4 (x100)","cat":"Bulonería y Tornillería","stock":80,"fv":[4.0,1.0,4.0,0.0,80,1900.0,16.0,0.0,1.0,20.0],"conv":[4.0,0.026,"bajo",false],"ia":[3.3,0.003,"bajo",false],"hib":[4.0,0.026,"bajo",false,"rapido"]},
    {"id":26,"n":"Arandela Grower 1/4 (x100)","cat":"Bulonería y Tornillería","stock":85,"fv":[0.0,0.0,0.0,0.0,85,1400.0,85.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[5.3,0.005,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":27,"n":"Guantes de Nitrilo Talle L","cat":"Seguridad Industrial","stock":75,"fv":[4.0,1.0,4.0,0.0,75,3100.0,15.0,0.0,1.0,18.75],"conv":[4.0,0.028,"bajo",false],"ia":[3.6,0.004,"bajo",false],"hib":[4.0,0.028,"bajo",false,"rapido"]},
    {"id":28,"n":"Casco de Seguridad Amarillo","cat":"Seguridad Industrial","stock":15,"fv":[0.0,0.0,0.0,0.0,15,9800.0,15.0,0.0,1.0,999.0],"conv":[0.0,0.0,"bajo",false],"ia":[8.0,0.175,"bajo",false],"hib":[0.0,0.0,"bajo",false,"rapido"]},
    {"id":29,"n":"Cinta Métrica 5m Antichoque","cat":"Ferretería y Herramientas","stock":40,"fv":[3.0,2.0,1.5,0.25,40,4900.0,10.0,0.0,2.0,26.67],"conv":[3.0,0.035,"bajo",false],"ia":[4.6,0.021,"bajo",false],"hib":[3.0,0.035,"bajo",false,"rapido"]},
    {"id":30,"n":"Sellador de Silicona Neutra 280ml","cat":"Pinturas y Adhesivos","stock":0,"fv":[2.0,1.0,2.0,0.0,0,6200.0,0.0,1.0,1.0,0.0],"conv":[2.0,1.0,"critico",true],"ia":[5.8,0.757,"critico",true],"hib":[5.8,0.757,"critico",true,"ia"]}
  ]
};
