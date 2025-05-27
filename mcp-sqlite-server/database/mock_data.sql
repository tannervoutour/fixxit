-- Mock Data for Machine Maintenance System

-- Insert technicians
INSERT INTO technicians (name, employee_id, expertise_areas, contact_info, certification_level, hire_date) VALUES
('John Martinez', 'EMP001', '["hydraulics", "electrical", "mechanical"]', 'john.martinez@company.com | Ext: 1234', 'expert', '2020-03-15'),
('Sarah Chen', 'EMP002', '["electrical", "plc", "automation"]', 'sarah.chen@company.com | Ext: 1235', 'senior', '2021-07-22'),
('Mike Johnson', 'EMP003', '["mechanical", "hydraulics", "welding"]', 'mike.johnson@company.com | Ext: 1236', 'senior', '2019-11-08'),
('Lisa Rodriguez', 'EMP004', '["electrical", "safety", "inspection"]', 'lisa.rodriguez@company.com | Ext: 1237', 'lead', '2018-05-12'),
('Tom Wilson', 'EMP005', '["mechanical", "bearings", "lubrication"]', 'tom.wilson@company.com | Ext: 1238', 'junior', '2023-01-30');

-- Insert machines
INSERT INTO machines (serial_number, model, manufacturer, location, install_date, status, last_maintenance, next_maintenance) VALUES
('SN001234', 'CNC-X200', 'Haas Automation', 'Building A - Floor 1', '2022-01-15', 'operational', '2024-05-15', '2024-08-15'),
('SN002345', 'PRESS-H500', 'Hydraulic Systems Inc', 'Building A - Floor 2', '2021-08-20', 'operational', '2024-05-10', '2024-08-10'),
('SN003456', 'CONV-B100', 'Belt Conveyor Co', 'Building B - Shipping', '2023-03-10', 'maintenance', '2024-05-20', '2024-06-20'),
('SN004567', 'CNC-X200', 'Haas Automation', 'Building A - Floor 1', '2022-05-30', 'operational', '2024-05-12', '2024-08-12'),
('SN005678', 'WELD-R300', 'Robotic Welding Corp', 'Building C - Assembly', '2020-12-05', 'down', '2024-04-30', '2024-06-01'),
('SN006789', 'PUMP-C150', 'Industrial Pumps Ltd', 'Building D - Utilities', '2019-09-18', 'operational', '2024-05-18', '2024-08-18'),
('SN007890', 'CONV-B100', 'Belt Conveyor Co', 'Building B - Receiving', '2023-01-25', 'operational', '2024-05-25', '2024-08-25'),
('SN008901', 'PRESS-H500', 'Hydraulic Systems Inc', 'Building A - Floor 3', '2021-11-12', 'operational', '2024-05-08', '2024-08-08');

-- Insert fault codes
INSERT INTO fault_codes (code, machine_model, description, severity, troubleshooting_steps, estimated_repair_time) VALUES
('E001', 'CNC-X200', 'Spindle motor overheating', 'high', '1. Check coolant levels\n2. Inspect air filters\n3. Verify fan operation\n4. Check thermal sensors', 120),
('E002', 'CNC-X200', 'Tool changer malfunction', 'medium', '1. Check pneumatic pressure\n2. Inspect tool changer arm\n3. Verify position sensors\n4. Lubricate mechanisms', 90),
('H001', 'PRESS-H500', 'Hydraulic pressure low', 'high', '1. Check hydraulic fluid level\n2. Inspect for leaks\n3. Test pressure relief valve\n4. Check pump operation', 60),
('H002', 'PRESS-H500', 'Ram position sensor fault', 'medium', '1. Clean sensor\n2. Check wiring connections\n3. Calibrate position\n4. Replace if necessary', 45),
('C001', 'CONV-B100', 'Belt misalignment', 'low', '1. Check belt tension\n2. Inspect pulleys\n3. Adjust tracking\n4. Lubricate bearings', 30),
('C002', 'CONV-B100', 'Motor overload', 'high', '1. Check load conditions\n2. Inspect motor connections\n3. Test motor insulation\n4. Check overload relay', 75),
('W001', 'WELD-R300', 'Arc instability', 'medium', '1. Check gas flow\n2. Inspect wire feed\n3. Clean contact tips\n4. Verify ground connection', 40),
('P001', 'PUMP-C150', 'Cavitation detected', 'high', '1. Check suction line\n2. Verify fluid level\n3. Inspect impeller\n4. Check NPSH conditions', 90);

-- Insert trouble tickets
INSERT INTO trouble_tickets (machine_id, reported_by, status, priority, fault_code, description, assigned_technician_id, resolved_date) VALUES
(1, 'Operator Smith', 'resolved', 'medium', 'E002', 'Tool changer not responding to commands, stuck between positions', 2, '2024-05-22 14:30:00'),
(2, 'Supervisor Jones', 'in_progress', 'high', 'H001', 'Hydraulic pressure dropping during operation, possible leak detected', 1, NULL),
(3, 'Maintenance Lead', 'open', 'high', 'C002', 'Conveyor motor tripping breaker repeatedly during startup', NULL, NULL),
(5, 'Operator Brown', 'assigned', 'urgent', 'W001', 'Welding robot producing poor quality welds, arc keeps breaking', 3, NULL),
(6, 'Facility Manager', 'resolved', 'medium', 'P001', 'Unusual noise from pump, vibration increasing', 4, '2024-05-20 09:15:00'),
(1, 'Quality Control', 'open', 'low', NULL, 'Dimensional accuracy slightly off specification on recent parts', NULL, NULL),
(4, 'Operator Davis', 'closed', 'medium', 'E001', 'Machine running hot, spindle temperature alarm triggered', 2, '2024-05-18 16:45:00');

-- Insert maintenance records
INSERT INTO maintenance_records (machine_id, technician_id, maintenance_date, maintenance_type, description, parts_used, labor_hours, status, notes) VALUES
(1, 2, '2024-05-15', 'preventive', 'Monthly preventive maintenance - lubrication and inspection', '["LUB-001", "FILTER-X200"]', 2.5, 'completed', 'All systems operating normally'),
(2, 1, '2024-05-10', 'preventive', 'Hydraulic system maintenance and fluid change', '["FLUID-H500", "SEAL-KIT-A"]', 4.0, 'completed', 'Replaced worn seals, system pressure stable'),
(3, 3, '2024-05-20', 'corrective', 'Belt alignment and tension adjustment', '["BELT-B100"]', 1.5, 'completed', 'Belt tracking corrected, running smoothly'),
(4, 2, '2024-05-12', 'preventive', 'Tool changer calibration and lubrication', '["LUB-001"]', 1.8, 'completed', 'Calibration within specifications'),
(5, 1, '2024-05-25', 'emergency', 'Investigate welding quality issues', '["CONTACT-TIP", "LINER-W300"]', 3.2, 'in_progress', 'Replaced consumables, testing in progress'),
(6, 4, '2024-05-18', 'corrective', 'Pump bearing replacement due to vibration', '["BEARING-C150", "COUPLING"]', 5.5, 'completed', 'Vibration eliminated, pump running quietly'),
(7, 5, '2024-05-25', 'preventive', 'Weekly conveyor inspection and lubrication', '["LUB-002"]', 0.8, 'completed', 'Routine maintenance completed'),
(8, 1, '2024-05-08', 'preventive', 'Hydraulic filter replacement and system check', '["FILTER-H500"]', 1.2, 'completed', 'Filter was due for replacement');

-- Insert parts inventory
INSERT INTO parts_inventory (part_number, name, description, compatible_models, stock_quantity, min_stock_level, storage_location, unit_cost, supplier, last_ordered) VALUES
('LUB-001', 'High-Temp Spindle Grease', 'High temperature bearing grease for CNC spindles', '["CNC-X200"]', 12, 5, 'Shelf A-1', 45.99, 'Industrial Lubricants Inc', '2024-04-15'),
('LUB-002', 'Chain & Belt Lubricant', 'Multi-purpose lubricant for conveyors', '["CONV-B100"]', 8, 3, 'Shelf A-2', 28.50, 'Industrial Lubricants Inc', '2024-05-01'),
('FILTER-X200', 'CNC Air Filter', 'HEPA air filter for CNC machine cooling system', '["CNC-X200"]', 6, 2, 'Shelf B-1', 89.99, 'Haas Automation', '2024-03-20'),
('FILTER-H500', 'Hydraulic Return Filter', 'High-pressure hydraulic return filter', '["PRESS-H500"]', 4, 2, 'Shelf B-2', 125.00, 'Hydraulic Systems Inc', '2024-05-10'),
('FLUID-H500', 'Hydraulic Fluid AW46', 'Anti-wear hydraulic fluid 5-gallon container', '["PRESS-H500", "PUMP-C150"]', 15, 8, 'Storage Room C', 78.50, 'Fluid Solutions Corp', '2024-04-28'),
('SEAL-KIT-A', 'Hydraulic Seal Kit', 'Complete seal kit for hydraulic cylinders', '["PRESS-H500"]', 3, 2, 'Drawer C-1', 156.75, 'Hydraulic Systems Inc', '2024-02-15'),
('BELT-B100', 'Conveyor Belt 24ft', 'Rubber conveyor belt with cleats', '["CONV-B100"]', 2, 1, 'Storage Room D', 445.00, 'Belt Conveyor Co', '2024-01-30'),
('BEARING-C150', 'Pump Bearing Set', 'Ball bearing set for centrifugal pumps', '["PUMP-C150"]', 4, 2, 'Drawer B-3', 198.25, 'Industrial Pumps Ltd', '2024-03-10'),
('CONTACT-TIP', 'Welding Contact Tips', 'Copper contact tips for MIG welding (pack of 10)', '["WELD-R300"]', 25, 10, 'Shelf D-1', 18.99, 'Robotic Welding Corp', '2024-05-15'),
('LINER-W300', 'Wire Feed Liner', 'Teflon liner for welding wire feed system', '["WELD-R300"]', 6, 3, 'Shelf D-2', 34.50, 'Robotic Welding Corp', '2024-04-20'),
('COUPLING', 'Flexible Coupling', 'Flexible coupling for motor-pump connection', '["PUMP-C150"]', 2, 1, 'Drawer B-4', 89.99, 'Industrial Pumps Ltd', '2024-05-05');