"""Response formatting utilities for better user experience."""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ResponseFormatter:
    """Formats responses from MCP tools for better readability."""
    
    def __init__(self, use_rich: bool = True):
        """Initialize formatter with optional rich formatting."""
        self.use_rich = use_rich and RICH_AVAILABLE
        if self.use_rich:
            self.console = Console()
    
    def format_function_result(self, function_name: str, result: Dict[str, Any]) -> str:
        """Format a function call result based on the function type."""
        if not result.get('success'):
            return self._format_error(result)
        
        data = result.get('result', {})
        
        # Route to specific formatters based on function
        formatters = {
            'search_equipment': self._format_machines,
            'get_maintenance_tickets': self._format_tickets,
            'get_service_history': self._format_maintenance_records,
            'search_parts_inventory': self._format_parts,
            'get_troubleshooting_help': self._format_fault_codes,
            'get_technician_info': self._format_technicians,
            'query_maintenance_database': self._format_query_results,
            'get_database_overview': self._format_overview
        }
        
        formatter = formatters.get(function_name, self._format_generic)
        return formatter(data)
    
    def _format_error(self, result: Dict[str, Any]) -> str:
        """Format error messages."""
        error_msg = result.get('error', 'Unknown error')
        
        if self.use_rich:
            return f"❌ **Error:** {error_msg}"
        else:
            return f"❌ Error: {error_msg}"
    
    def _format_machines(self, data: Dict[str, Any]) -> str:
        """Format machine search results."""
        machines = data.get('machines', [])
        count = data.get('machine_count', len(machines))
        
        if count == 0:
            return "No machines found matching the criteria."
        
        if self.use_rich:
            return self._format_machines_rich(machines, count)
        else:
            return self._format_machines_plain(machines, count)
    
    def _format_machines_rich(self, machines: List[Dict], count: int) -> str:
        """Format machines with rich formatting."""
        output = f"**Found {count} machine(s):**\\n\\n"
        
        for machine in machines:
            status_emoji = {
                'operational': '✅',
                'maintenance': '🔧', 
                'down': '❌',
                'retired': '📦'
            }.get(machine.get('status', ''), '❓')
            
            output += f"{status_emoji} **{machine.get('model', 'Unknown')}** "
            output += f"({machine.get('serial_number', 'No SN')})\\n"
            output += f"   📍 Location: {machine.get('location', 'Unknown')}\\n"
            output += f"   🏭 Manufacturer: {machine.get('manufacturer', 'Unknown')}\\n"
            output += f"   📊 Status: {machine.get('status', 'Unknown')}\\n"
            
            if machine.get('next_maintenance'):
                output += f"   🗓️ Next Maintenance: {machine.get('next_maintenance')}\\n"
            
            output += "\\n"
        
        return output
    
    def _format_machines_plain(self, machines: List[Dict], count: int) -> str:
        """Format machines with plain text."""
        output = f"Found {count} machine(s):\\n\\n"
        
        for i, machine in enumerate(machines, 1):
            output += f"{i}. {machine.get('model', 'Unknown')} ({machine.get('serial_number', 'No SN')})\\n"
            output += f"   Location: {machine.get('location', 'Unknown')}\\n"
            output += f"   Manufacturer: {machine.get('manufacturer', 'Unknown')}\\n"
            output += f"   Status: {machine.get('status', 'Unknown')}\\n"
            
            if machine.get('next_maintenance'):
                output += f"   Next Maintenance: {machine.get('next_maintenance')}\\n"
            
            output += "\\n"
        
        return output
    
    def _format_tickets(self, data: Dict[str, Any]) -> str:
        """Format trouble ticket results."""
        tickets = data.get('tickets', [])
        count = data.get('ticket_count', len(tickets))
        
        if count == 0:
            return "No trouble tickets found matching the criteria."
        
        output = f"**Found {count} trouble ticket(s):**\\n\\n"
        
        for ticket in tickets:
            priority_emoji = {
                'urgent': '🚨',
                'high': '⚠️',
                'medium': '📋',
                'low': '📝'
            }.get(ticket.get('priority', ''), '📋')
            
            status_emoji = {
                'open': '🔓',
                'assigned': '👤',
                'in_progress': '⚙️',
                'resolved': '✅',
                'closed': '🔒'
            }.get(ticket.get('status', ''), '❓')
            
            output += f"{priority_emoji} {status_emoji} **Ticket #{ticket.get('id')}** - {ticket.get('priority', 'medium').upper()}\\n"
            output += f"   🏭 Machine: {ticket.get('model', 'Unknown')} ({ticket.get('serial_number', 'No SN')})\\n"
            output += f"   📍 Location: {ticket.get('location', 'Unknown')}\\n"
            output += f"   👤 Reported by: {ticket.get('reported_by', 'Unknown')}\\n"
            output += f"   📅 Date: {ticket.get('date_reported', 'Unknown')}\\n"
            
            if ticket.get('fault_code'):
                output += f"   🔍 Fault Code: {ticket.get('fault_code')}\\n"
            
            if ticket.get('assigned_technician'):
                output += f"   🔧 Assigned to: {ticket.get('assigned_technician')}\\n"
            
            description = ticket.get('description', '')
            if description:
                # Truncate long descriptions
                if len(description) > 100:
                    description = description[:100] + "..."
                output += f"   📝 Issue: {description}\\n"
            
            output += "\\n"
        
        return output
    
    def _format_maintenance_records(self, data: Dict[str, Any]) -> str:
        """Format maintenance history results."""
        records = data.get('maintenance_records', [])
        count = data.get('record_count', len(records))
        
        if count == 0:
            return "No maintenance records found matching the criteria."
        
        output = f"**Found {count} maintenance record(s):**\\n\\n"
        
        for record in records:
            type_emoji = {
                'preventive': '🗓️',
                'corrective': '🔧',
                'emergency': '🚨',
                'inspection': '🔍'
            }.get(record.get('maintenance_type', ''), '🔧')
            
            output += f"{type_emoji} **{record.get('maintenance_type', 'Unknown').title()} Maintenance**\\n"
            output += f"   🏭 Machine: {record.get('model', 'Unknown')} ({record.get('serial_number', 'No SN')})\\n"
            output += f"   📍 Location: {record.get('location', 'Unknown')}\\n"
            output += f"   👤 Technician: {record.get('technician_name', 'Unknown')}\\n"
            output += f"   📅 Date: {record.get('maintenance_date', 'Unknown')}\\n"
            output += f"   ⏱️ Labor Hours: {record.get('labor_hours', 'Unknown')}\\n"
            
            description = record.get('description', '')
            if description:
                if len(description) > 100:
                    description = description[:100] + "..."
                output += f"   📝 Work: {description}\\n"
            
            output += "\\n"
        
        return output
    
    def _format_parts(self, data: Dict[str, Any]) -> str:
        """Format parts inventory results."""
        parts = data.get('parts', [])
        count = data.get('parts_count', len(parts))
        
        if count == 0:
            return "No parts found matching the criteria."
        
        output = f"**Found {count} part(s):**\\n\\n"
        
        for part in parts:
            stock_status = part.get('stock_status', 'OK')
            status_emoji = '⚠️' if stock_status == 'LOW' else '✅'
            
            output += f"{status_emoji} **{part.get('name', 'Unknown')}** ({part.get('part_number', 'No PN')})\\n"
            output += f"   📦 Stock: {part.get('stock_quantity', 0)} (min: {part.get('min_stock_level', 0)})\\n"
            output += f"   📍 Location: {part.get('storage_location', 'Unknown')}\\n"
            output += f"   💰 Cost: ${part.get('unit_cost', 0):.2f}\\n"
            
            if part.get('supplier'):
                output += f"   🏢 Supplier: {part.get('supplier')}\\n"
            
            compatible = part.get('compatible_models', '')
            if compatible:
                # Parse JSON if it's a string
                try:
                    if isinstance(compatible, str):
                        compatible_list = json.loads(compatible)
                        compatible = ', '.join(compatible_list)
                except:
                    pass
                output += f"   🔧 Compatible: {compatible}\\n"
            
            output += "\\n"
        
        return output
    
    def _format_fault_codes(self, data: Dict[str, Any]) -> str:
        """Format fault code information."""
        if 'fault_code' in data and 'details' in data:
            # Single fault code
            return self._format_single_fault_code(data['details'])
        elif 'fault_codes' in data:
            # Multiple fault codes
            codes = data['fault_codes']
            count = data.get('total_codes', len(codes))
            
            output = f"**Found {count} fault code(s):**\\n\\n"
            
            for code in codes:
                severity_emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '📋',
                    'low': '📝'
                }.get(code.get('severity', ''), '📋')
                
                output += f"{severity_emoji} **{code.get('code', 'Unknown')}** - {code.get('severity', 'medium').upper()}\\n"
                output += f"   🏭 Model: {code.get('machine_model', 'Unknown')}\\n"
                output += f"   📝 Issue: {code.get('description', 'No description')}\\n"
                
                if code.get('estimated_repair_time'):
                    output += f"   ⏱️ Est. Repair Time: {code.get('estimated_repair_time')} minutes\\n"
                
                output += "\\n"
            
            return output
        
        return "No fault code information available."
    
    def _format_single_fault_code(self, details: Dict[str, Any]) -> str:
        """Format a single fault code with troubleshooting steps."""
        code = details.get('code', 'Unknown')
        severity = details.get('severity', 'medium')
        
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️', 
            'medium': '📋',
            'low': '📝'
        }.get(severity, '📋')
        
        output = f"{severity_emoji} **Fault Code {code}** - {severity.upper()} Priority\\n\\n"
        output += f"🏭 **Machine Model:** {details.get('machine_model', 'Unknown')}\\n"
        output += f"📝 **Description:** {details.get('description', 'No description')}\\n"
        
        if details.get('estimated_repair_time'):
            output += f"⏱️ **Estimated Repair Time:** {details.get('estimated_repair_time')} minutes\\n"
        
        steps = details.get('troubleshooting_steps', '')
        if steps:
            output += f"\\n🔧 **Troubleshooting Steps:**\\n{steps}\\n"
        
        return output
    
    def _format_technicians(self, data: Dict[str, Any]) -> str:
        """Format technician information."""
        if 'technician' in data:
            # Single technician
            return self._format_single_technician(data['technician'], data.get('recent_work_stats'))
        elif 'technicians' in data:
            # Multiple technicians
            technicians = data['technicians']
            count = data.get('active_technicians', len(technicians))
            
            output = f"**Found {count} active technician(s):**\\n\\n"
            
            for tech in technicians:
                cert_emoji = {
                    'lead': '👑',
                    'expert': '🥇',
                    'senior': '🥈',
                    'junior': '🥉'
                }.get(tech.get('certification_level', ''), '👤')
                
                output += f"{cert_emoji} **{tech.get('name', 'Unknown')}** ({tech.get('employee_id', 'No ID')})\\n"
                output += f"   🎓 Level: {tech.get('certification_level', 'Unknown').title()}\\n"
                output += f"   📅 Hire Date: {tech.get('hire_date', 'Unknown')}\\n"
                
                expertise = tech.get('expertise_areas', '')
                if expertise:
                    try:
                        if isinstance(expertise, str):
                            expertise_list = json.loads(expertise)
                            expertise = ', '.join(expertise_list)
                    except:
                        pass
                    output += f"   🔧 Expertise: {expertise}\\n"
                
                output += "\\n"
            
            return output
        
        return "No technician information available."
    
    def _format_single_technician(self, tech: Dict[str, Any], work_stats: Optional[Dict[str, Any]] = None) -> str:
        """Format a single technician with detailed information."""
        cert_emoji = {
            'lead': '👑',
            'expert': '🥇',
            'senior': '🥈', 
            'junior': '🥉'
        }.get(tech.get('certification_level', ''), '👤')
        
        output = f"{cert_emoji} **{tech.get('name', 'Unknown')}** ({tech.get('employee_id', 'No ID')})\\n\\n"
        output += f"🎓 **Certification Level:** {tech.get('certification_level', 'Unknown').title()}\\n"
        output += f"📞 **Contact:** {tech.get('contact_info', 'No contact info')}\\n"
        output += f"📅 **Hire Date:** {tech.get('hire_date', 'Unknown')}\\n"
        
        expertise = tech.get('expertise_areas', '')
        if expertise:
            try:
                if isinstance(expertise, str):
                    expertise_list = json.loads(expertise)
                    expertise = ', '.join(expertise_list)
            except:
                pass
            output += f"🔧 **Expertise Areas:** {expertise}\\n"
        
        if work_stats:
            output += f"\\n📊 **Recent Work (Last 30 Days):**\\n"
            output += f"   🔧 Jobs Completed: {work_stats.get('total_jobs', 0)}\\n"
            if work_stats.get('avg_hours'):
                output += f"   ⏱️ Avg Hours per Job: {work_stats.get('avg_hours', 0):.1f}\\n"
            if work_stats.get('last_job_date'):
                output += f"   📅 Last Job: {work_stats.get('last_job_date')}\\n"
        
        return output
    
    def _format_query_results(self, data: Dict[str, Any]) -> str:
        """Format custom query results."""
        results = data.get('results', [])
        count = data.get('row_count', len(results))
        query = data.get('query', '')
        
        if count == 0:
            return "Query returned no results."
        
        output = f"**Query Results ({count} row(s)):**\\n"
        if query:
            output += f"Query: `{query}`\\n\\n"
        
        if results:
            # Show first few results in a readable format
            for i, row in enumerate(results[:10], 1):  # Limit to 10 rows
                output += f"**Row {i}:**\\n"
                for key, value in row.items():
                    output += f"   {key}: {value}\\n"
                output += "\\n"
            
            if len(results) > 10:
                output += f"... and {len(results) - 10} more rows\\n"
        
        return output
    
    def _format_overview(self, data: Dict[str, Any]) -> str:
        """Format database overview/statistics."""
        stats = data.get('statistics', {})
        
        output = "📊 **Maintenance System Overview**\\n\\n"
        
        # Machine stats
        machine_stats = stats.get('maintenance_insights', {}).get('machine_status_distribution', {})
        if machine_stats:
            output += "🏭 **Machine Status:**\\n"
            for status, count in machine_stats.items():
                emoji = {'operational': '✅', 'maintenance': '🔧', 'down': '❌', 'retired': '📦'}.get(status, '❓')
                output += f"   {emoji} {status.title()}: {count}\\n"
            output += "\\n"
        
        # Ticket stats
        ticket_stats = stats.get('maintenance_insights', {}).get('recent_tickets_by_status', {})
        if ticket_stats:
            output += "🎫 **Recent Tickets (Last 7 Days):**\\n"
            for status, count in ticket_stats.items():
                emoji = {'open': '🔓', 'assigned': '👤', 'in_progress': '⚙️', 'resolved': '✅'}.get(status, '📋')
                output += f"   {emoji} {status.title()}: {count}\\n"
            output += "\\n"
        
        # Parts status
        low_stock = stats.get('maintenance_insights', {}).get('low_stock_parts_count', 0)
        if low_stock > 0:
            output += f"📦 **Parts Status:** ⚠️ {low_stock} parts below minimum stock level\\n\\n"
        else:
            output += "📦 **Parts Status:** ✅ All parts adequately stocked\\n\\n"
        
        # Overdue maintenance
        overdue = stats.get('maintenance_insights', {}).get('overdue_maintenance_count', 0)
        if overdue > 0:
            output += f"🗓️ **Maintenance Status:** ⚠️ {overdue} machines overdue for maintenance\\n\\n"
        else:
            output += "🗓️ **Maintenance Status:** ✅ All maintenance up to date\\n\\n"
        
        return output
    
    def _format_generic(self, data: Dict[str, Any]) -> str:
        """Generic formatter for unknown data types."""
        return f"**Result:**\\n```json\\n{json.dumps(data, indent=2)}\\n```"


# Global formatter instance
formatter = ResponseFormatter()