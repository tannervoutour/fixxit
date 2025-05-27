-- Machine Maintenance Database Schema

-- Equipment/Machine inventory
CREATE TABLE machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    location TEXT NOT NULL,
    install_date DATE NOT NULL,
    status TEXT CHECK(status IN ('operational', 'maintenance', 'down', 'retired')) DEFAULT 'operational',
    last_maintenance DATE,
    next_maintenance DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technician information
CREATE TABLE technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    employee_id TEXT UNIQUE NOT NULL,
    expertise_areas TEXT NOT NULL, -- JSON array of specialties
    contact_info TEXT NOT NULL,
    certification_level TEXT CHECK(certification_level IN ('junior', 'senior', 'expert', 'lead')) DEFAULT 'junior',
    hire_date DATE NOT NULL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fault code definitions
CREATE TABLE fault_codes (
    code TEXT PRIMARY KEY,
    machine_model TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    troubleshooting_steps TEXT NOT NULL,
    estimated_repair_time INTEGER, -- minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance history records
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,
    technician_id INTEGER NOT NULL,
    maintenance_date DATE NOT NULL,
    maintenance_type TEXT CHECK(maintenance_type IN ('preventive', 'corrective', 'emergency', 'inspection')) DEFAULT 'preventive',
    description TEXT NOT NULL,
    parts_used TEXT, -- JSON array of part numbers and quantities
    labor_hours REAL NOT NULL,
    status TEXT CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (technician_id) REFERENCES technicians(id)
);

-- Trouble ticket tracking
CREATE TABLE trouble_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,
    reported_by TEXT NOT NULL,
    date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('open', 'assigned', 'in_progress', 'resolved', 'closed')) DEFAULT 'open',
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
    fault_code TEXT,
    description TEXT NOT NULL,
    resolution TEXT,
    assigned_technician_id INTEGER,
    resolved_date TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (fault_code) REFERENCES fault_codes(code),
    FOREIGN KEY (assigned_technician_id) REFERENCES technicians(id)
);

-- Parts inventory management
CREATE TABLE parts_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    compatible_models TEXT NOT NULL, -- JSON array of compatible machine models
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    min_stock_level INTEGER NOT NULL DEFAULT 5,
    storage_location TEXT NOT NULL,
    unit_cost REAL NOT NULL,
    supplier TEXT,
    last_ordered DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_location ON machines(location);
CREATE INDEX idx_machines_model ON machines(model);
CREATE INDEX idx_trouble_tickets_status ON trouble_tickets(status);
CREATE INDEX idx_trouble_tickets_priority ON trouble_tickets(priority);
CREATE INDEX idx_maintenance_records_date ON maintenance_records(maintenance_date);
CREATE INDEX idx_fault_codes_severity ON fault_codes(severity);
CREATE INDEX idx_parts_inventory_stock ON parts_inventory(stock_quantity);