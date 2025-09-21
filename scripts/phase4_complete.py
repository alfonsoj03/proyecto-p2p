#!/usr/bin/env python3
"""
Script completo para la Fase 4 - Concurrencia y Tolerancia a Fallos.
Ejecuta todas las pruebas de la Fase 4 y genera un reporte final.
"""
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

# Importar módulos de prueba de la Fase 4
from concurrency_test import ConcurrencyTester
from fault_tolerance_test import FaultToleranceTester
from performance_metrics import PerformanceMonitor

class Phase4CompleteTest:
    """Coordinador completo de pruebas de la Fase 4."""
    
    def __init__(self):
        self.test_results = {
            "phase4_summary": {
                "start_time": None,
                "end_time": None,
                "total_duration": 0,
                "tests_executed": [],
                "overall_success": False
            },
            "concurrency_results": {},
            "fault_tolerance_results": {},
            "performance_results": {},
            "final_assessment": {}
        }
    
    async def run_complete_phase4_test(self):
        """Ejecuta la suite completa de pruebas de la Fase 4."""
        print("🚀 INICIANDO FASE 4 COMPLETA - CONCURRENCIA Y TOLERANCIA A FALLOS")
        print("="*80)
        
        start_time = time.time()
        self.test_results["phase4_summary"]["start_time"] = datetime.now().isoformat()
        
        try:
            # Verificar estado inicial de la red
            if not await self._verify_initial_network_state():
                print("❌ Red P2P no está en estado adecuado para pruebas")
                return False
            
            # Fase 4.1: Pruebas de Concurrencia
            print("\n" + "🔄 FASE 4.1 - PRUEBAS DE CONCURRENCIA" + "="*50)
            concurrency_success = await self._run_concurrency_tests()
            self.test_results["phase4_summary"]["tests_executed"].append("concurrency")
            
            # Pausa entre fases
            await asyncio.sleep(5)
            
            # Fase 4.2: Tolerancia a Fallos
            print("\n" + "🛡️  FASE 4.2 - TOLERANCIA A FALLOS" + "="*50)
            fault_tolerance_success = await self._run_fault_tolerance_tests()
            self.test_results["phase4_summary"]["tests_executed"].append("fault_tolerance")
            
            # Pausa entre fases
            await asyncio.sleep(5)
            
            # Fase 4.3: Análisis de Rendimiento
            print("\n" + "📊 FASE 4.3 - ANÁLISIS DE RENDIMIENTO" + "="*50)
            performance_success = await self._run_performance_analysis()
            self.test_results["phase4_summary"]["tests_executed"].append("performance")
            
            # Fase 4.4: Evaluación Final
            print("\n" + "📈 FASE 4.4 - EVALUACIÓN FINAL" + "="*50)
            final_assessment = await self._conduct_final_assessment()
            
            # Determinar éxito general
            overall_success = all([
                concurrency_success,
                fault_tolerance_success, 
                performance_success,
                final_assessment["system_ready_for_production"]
            ])
            
            self.test_results["phase4_summary"]["overall_success"] = overall_success
            
        except Exception as e:
            print(f"❌ Error durante ejecución de Fase 4: {e}")
            overall_success = False
        
        finally:
            # Finalizar y generar reporte
            end_time = time.time()
            self.test_results["phase4_summary"]["end_time"] = datetime.now().isoformat()
            self.test_results["phase4_summary"]["total_duration"] = end_time - start_time
            
            await self._generate_final_report()
            
            return overall_success
    
    async def _verify_initial_network_state(self) -> bool:
        """Verifica que la red P2P esté en estado adecuado."""
        print("🔍 Verificando estado inicial de la red P2P...")
        
        nodes = {
            "peer1": "127.0.0.1:50001",
            "peer2": "127.0.0.1:50002",
            "peer3": "127.0.0.1:50003"
        }
        
        # Usar el monitor de rendimiento para verificar salud
        monitor = PerformanceMonitor()
        snapshot = await monitor._take_metrics_snapshot()
        
        if snapshot.active_nodes < 3:
            print(f"⚠️  Solo {snapshot.active_nodes}/3 nodos activos")
            print("Ejecuta: python scripts/start_nodes.py")
            return False
        
        print(f"✅ Red verificada: {snapshot.active_nodes}/3 nodos activos")
        
        # Verificar funcionalidad básica
        from scripts.test_client import P2PTestClient
        client = P2PTestClient()
        
        # Probar búsqueda básica
        search_result = await client.search_file(nodes["peer1"], "video_especial.mp4")
        if not search_result.get("success"):
            print("❌ Funcionalidad de búsqueda no operativa")
            return False
        
        print("✅ Funcionalidad básica verificada")
        return True
    
    async def _run_concurrency_tests(self) -> bool:
        """Ejecuta pruebas de concurrencia."""
        try:
            tester = ConcurrencyTester()
            
            # Ejecutar pruebas de concurrencia con diferentes niveles
            concurrency_levels = [5, 10, 20]
            
            for level in concurrency_levels:
                print(f"\n🔄 Prueba de concurrencia - Nivel {level}")
                
                # Búsquedas concurrentes
                search_results = await tester.concurrent_searches(level)
                
                # Indexaciones concurrentes  
                index_results = await tester.concurrent_indexing(level)
                
                # Descargas concurrentes (si gRPC está disponible)
                try:
                    download_results = await tester.concurrent_downloads(min(level, 5))
                except Exception as e:
                    print(f"⚠️  Descargas gRPC no disponibles: {e}")
                    download_results = {}
                
                await asyncio.sleep(2)
            
            # Guardar resultados
            tester.save_results("phase4_concurrency_results.json")
            self.test_results["concurrency_results"] = tester.results
            
            # Evaluar éxito (tasa de éxito > 80% en todas las pruebas)
            success_rates = []
            for result_type in ["searches", "indexing", "downloads"]:
                if tester.results[result_type]:
                    rates = [r["success_rate"] for r in tester.results[result_type]]
                    success_rates.extend(rates)
            
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
            concurrency_success = avg_success_rate >= 80.0
            
            print(f"📊 Tasa de éxito promedio en concurrencia: {avg_success_rate:.1f}%")
            print(f"{'✅' if concurrency_success else '❌'} Pruebas de concurrencia: {'EXITOSAS' if concurrency_success else 'FALLIDAS'}")
            
            return concurrency_success
            
        except Exception as e:
            print(f"❌ Error en pruebas de concurrencia: {e}")
            return False
    
    async def _run_fault_tolerance_tests(self) -> bool:
        """Ejecuta pruebas de tolerancia a fallos."""
        try:
            tester = FaultToleranceTester()
            
            # Pruebas de recuperación de nodos
            node_failure_results = await tester.test_node_failure_recovery()
            
            # Pruebas de partición de red
            partition_results = await tester.test_network_partition_tolerance()
            
            # Pruebas de estrés gradual
            stress_results = await tester.test_gradual_node_stress()
            
            # Guardar resultados
            tester.save_results("phase4_fault_tolerance_results.json")
            self.test_results["fault_tolerance_results"] = tester.fault_results
            
            # Evaluar éxito
            node_failures_survived = all(r["network_survived"] for r in node_failure_results)
            full_recovery = all(r["full_recovery"] for r in node_failure_results)
            partition_recovery = partition_results.get("recovery_successful", False)
            stress_resilience = all(r["network_healthy"] for r in stress_results)
            
            fault_tolerance_success = all([
                node_failures_survived,
                full_recovery,
                partition_recovery,
                stress_resilience
            ])
            
            print(f"🛡️  Red sobrevivió fallos de nodos: {'✅' if node_failures_survived else '❌'}")
            print(f"🔄 Recuperación completa: {'✅' if full_recovery else '❌'}")
            print(f"🌐 Tolerancia a particiones: {'✅' if partition_recovery else '❌'}")
            print(f"💪 Resistencia a estrés: {'✅' if stress_resilience else '❌'}")
            print(f"{'✅' if fault_tolerance_success else '❌'} Tolerancia a fallos: {'EXITOSA' if fault_tolerance_success else 'FALLIDA'}")
            
            return fault_tolerance_success
            
        except Exception as e:
            print(f"❌ Error en pruebas de tolerancia a fallos: {e}")
            return False
    
    async def _run_performance_analysis(self) -> bool:
        """Ejecuta análisis de rendimiento."""
        try:
            monitor = PerformanceMonitor(monitoring_duration=180)  # 3 minutos
            
            # Monitoreo continuo
            await monitor.start_continuous_monitoring()
            
            # Benchmark de operaciones
            benchmark_results = await monitor.benchmark_operations()
            
            # Medición de latencia
            latency_matrix = await monitor.measure_network_latency()
            
            self.test_results["performance_results"] = {
                "benchmark_results": benchmark_results,
                "latency_matrix": latency_matrix,
                "monitoring_completed": True
            }
            
            # Evaluar rendimiento
            search_performance = benchmark_results.get("search_operations", {})
            search_ops_per_sec = search_performance.get("ops_per_second", 0)
            avg_response_time = search_performance.get("avg_time", float('inf'))
            
            # Criterios de éxito: > 10 búsquedas/seg y < 1s respuesta promedio
            performance_success = search_ops_per_sec >= 10.0 and avg_response_time <= 1.0
            
            print(f"🚀 Búsquedas por segundo: {search_ops_per_sec:.1f}")
            print(f"⚡ Tiempo de respuesta promedio: {avg_response_time:.3f}s")
            print(f"{'✅' if performance_success else '❌'} Análisis de rendimiento: {'EXITOSO' if performance_success else 'INSUFICIENTE'}")
            
            return performance_success
            
        except Exception as e:
            print(f"❌ Error en análisis de rendimiento: {e}")
            return False
    
    async def _conduct_final_assessment(self) -> Dict[str, Any]:
        """Conduce evaluación final del sistema."""
        print("🎯 Realizando evaluación final del sistema P2P...")
        
        # Criterios de evaluación
        assessment_criteria = {
            "concurrency_support": False,
            "fault_tolerance": False,
            "performance_acceptable": False,
            "scalability_ready": False,
            "production_ready": False
        }
        
        # Evaluar concurrencia
        concurrency_results = self.test_results.get("concurrency_results", {})
        if concurrency_results.get("searches"):
            avg_concurrency_success = sum(r["success_rate"] for r in concurrency_results["searches"]) / len(concurrency_results["searches"])
            assessment_criteria["concurrency_support"] = avg_concurrency_success >= 85.0
        
        # Evaluar tolerancia a fallos
        fault_results = self.test_results.get("fault_tolerance_results", {})
        node_failures = fault_results.get("node_failures", [])
        if node_failures:
            fault_success = all(r["network_survived"] and r["full_recovery"] for r in node_failures)
            assessment_criteria["fault_tolerance"] = fault_success
        
        # Evaluar rendimiento
        performance_results = self.test_results.get("performance_results", {})
        benchmark = performance_results.get("benchmark_results", {})
        if benchmark.get("search_operations"):
            ops_per_sec = benchmark["search_operations"].get("ops_per_second", 0)
            assessment_criteria["performance_acceptable"] = ops_per_sec >= 10.0
        
        # Evaluar escalabilidad (basado en rendimiento bajo estrés)
        if fault_results.get("resilience_metrics"):
            stress_tests = fault_results["resilience_metrics"]
            high_stress_success = any(r["success_rate"] >= 70.0 and r["stress_level"] >= 20 for r in stress_tests)
            assessment_criteria["scalability_ready"] = high_stress_success
        
        # Evaluación general para producción
        assessment_criteria["production_ready"] = all([
            assessment_criteria["concurrency_support"],
            assessment_criteria["fault_tolerance"],
            assessment_criteria["performance_acceptable"]
        ])
        
        # Mostrar evaluación
        print("\n📋 EVALUACIÓN FINAL:")
        print(f"🔄 Soporte de concurrencia: {'✅' if assessment_criteria['concurrency_support'] else '❌'}")
        print(f"🛡️  Tolerancia a fallos: {'✅' if assessment_criteria['fault_tolerance'] else '❌'}")
        print(f"⚡ Rendimiento aceptable: {'✅' if assessment_criteria['performance_acceptable'] else '❌'}")
        print(f"📈 Listo para escalabilidad: {'✅' if assessment_criteria['scalability_ready'] else '❌'}")
        print(f"🚀 Listo para producción: {'✅' if assessment_criteria['production_ready'] else '❌'}")
        
        final_assessment = {
            "criteria": assessment_criteria,
            "system_ready_for_production": assessment_criteria["production_ready"],
            "recommendations": self._generate_recommendations(assessment_criteria)
        }
        
        self.test_results["final_assessment"] = final_assessment
        return final_assessment
    
    def _generate_recommendations(self, criteria: Dict[str, bool]) -> List[str]:
        """Genera recomendaciones basadas en los criterios de evaluación."""
        recommendations = []
        
        if not criteria["concurrency_support"]:
            recommendations.append("Mejorar manejo de concurrencia - considerar pool de conexiones")
        
        if not criteria["fault_tolerance"]:
            recommendations.append("Implementar mecanismos adicionales de recuperación automática")
        
        if not criteria["performance_acceptable"]:
            recommendations.append("Optimizar algoritmos de búsqueda y comunicación entre nodos")
        
        if not criteria["scalability_ready"]:
            recommendations.append("Implementar balanceador de carga y manejo de nodos dinámico")
        
        if criteria["production_ready"]:
            recommendations.append("Sistema listo para deployment - considerar monitoreo continuo")
        else:
            recommendations.append("Resolver issues críticos antes de deployment en producción")
        
        return recommendations
    
    async def _generate_final_report(self):
        """Genera reporte final completo de la Fase 4."""
        print("\n📊 GENERANDO REPORTE FINAL DE LA FASE 4...")
        
        # Guardar resultados completos
        with open("phase4_complete_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generar reporte en texto plano
        report_path = "PHASE4_FINAL_REPORT.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# REPORTE FINAL - FASE 4: CONCURRENCIA Y TOLERANCIA A FALLOS\n\n")
            
            f.write("## 📋 Resumen Ejecutivo\n\n")
            summary = self.test_results["phase4_summary"]
            f.write(f"- **Duración total**: {summary['total_duration']:.1f} segundos\n")
            f.write(f"- **Pruebas ejecutadas**: {', '.join(summary['tests_executed'])}\n")
            f.write(f"- **Éxito general**: {'✅ SÍ' if summary['overall_success'] else '❌ NO'}\n\n")
            
            f.write("## 🔄 Resultados de Concurrencia\n\n")
            concurrency = self.test_results.get("concurrency_results", {})
            if concurrency.get("searches"):
                avg_search_success = sum(r["success_rate"] for r in concurrency["searches"]) / len(concurrency["searches"])
                f.write(f"- **Tasa de éxito promedio en búsquedas**: {avg_search_success:.1f}%\n")
            
            f.write("\n## 🛡️ Resultados de Tolerancia a Fallos\n\n")
            fault_tolerance = self.test_results.get("fault_tolerance_results", {})
            node_failures = fault_tolerance.get("node_failures", [])
            if node_failures:
                survived_all = all(r["network_survived"] for r in node_failures)
                recovered_all = all(r["full_recovery"] for r in node_failures)
                f.write(f"- **Red sobrevivió a todos los fallos**: {'✅ SÍ' if survived_all else '❌ NO'}\n")
                f.write(f"- **Recuperación completa**: {'✅ SÍ' if recovered_all else '❌ NO'}\n")
            
            f.write("\n## 📊 Resultados de Rendimiento\n\n")
            performance = self.test_results.get("performance_results", {})
            benchmark = performance.get("benchmark_results", {})
            if benchmark.get("search_operations"):
                ops_per_sec = benchmark["search_operations"].get("ops_per_second", 0)
                avg_time = benchmark["search_operations"].get("avg_time", 0)
                f.write(f"- **Búsquedas por segundo**: {ops_per_sec:.1f}\n")
                f.write(f"- **Tiempo promedio de respuesta**: {avg_time:.3f}s\n")
            
            f.write("\n## 🎯 Evaluación Final\n\n")
            assessment = self.test_results.get("final_assessment", {})
            if assessment.get("criteria"):
                for criterion, passed in assessment["criteria"].items():
                    f.write(f"- **{criterion.replace('_', ' ').title()}**: {'✅ CUMPLE' if passed else '❌ NO CUMPLE'}\n")
            
            f.write("\n## 💡 Recomendaciones\n\n")
            recommendations = assessment.get("recommendations", [])
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"📊 Reporte final guardado en: {report_path}")
        print(f"📊 Datos completos en: phase4_complete_results.json")

async def main():
    """Función principal para ejecutar la Fase 4 completa."""
    phase4_tester = Phase4CompleteTest()
    
    success = await phase4_tester.run_complete_phase4_test()
    
    print("\n" + "="*80)
    if success:
        print("🎉 FASE 4 COMPLETADA EXITOSAMENTE")
        print("✅ El sistema P2P está listo para concurrencia y tolerancia a fallos")
    else:
        print("❌ FASE 4 COMPLETADA CON ISSUES")
        print("⚠️  Revisar reporte para identificar áreas de mejora")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
