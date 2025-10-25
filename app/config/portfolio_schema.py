"""
Database schema for Passive Income Portfolio Builder feature.
Contains SQL definitions for user profiles, portfolio groups, and positions.
"""

# Note: Each statement must be semicolon-terminated and work independently
CREATE_PORTFOLIO_TABLES_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_profiles')
    CREATE TABLE dbo.user_profiles (
        user_id INT IDENTITY(1,1) PRIMARY KEY,
        email NVARCHAR(255) NOT NULL UNIQUE,
        name NVARCHAR(255),
        created_at DATETIME2 DEFAULT GETDATE()
    );

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_user_email' AND object_id = OBJECT_ID('dbo.user_profiles'))
    CREATE INDEX idx_user_email ON dbo.user_profiles(email);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'portfolio_groups')
    CREATE TABLE dbo.portfolio_groups (
        group_id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT,
        name NVARCHAR(255) NOT NULL,
        type NVARCHAR(50) NOT NULL CHECK (type IN ('portfolio', 'watchlist')),
        metadata NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE()
    );

IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'fk_group_user')
    ALTER TABLE dbo.portfolio_groups ADD CONSTRAINT fk_group_user FOREIGN KEY (user_id) REFERENCES dbo.user_profiles(user_id) ON DELETE CASCADE;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_user' AND object_id = OBJECT_ID('dbo.portfolio_groups'))
    CREATE INDEX idx_group_user ON dbo.portfolio_groups(user_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_type' AND object_id = OBJECT_ID('dbo.portfolio_groups'))
    CREATE INDEX idx_group_type ON dbo.portfolio_groups(type);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'portfolio_positions')
    CREATE TABLE dbo.portfolio_positions (
        position_id INT IDENTITY(1,1) PRIMARY KEY,
        group_id INT NOT NULL,
        ticker NVARCHAR(50) NOT NULL,
        shares DECIMAL(18, 4),
        target_allocation_pct DECIMAL(5, 2),
        notes NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE()
    );

IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'fk_position_group')
    ALTER TABLE dbo.portfolio_positions ADD CONSTRAINT fk_position_group FOREIGN KEY (group_id) REFERENCES dbo.portfolio_groups(group_id) ON DELETE CASCADE;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_position_group' AND object_id = OBJECT_ID('dbo.portfolio_positions'))
    CREATE INDEX idx_position_group ON dbo.portfolio_positions(group_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_position_ticker' AND object_id = OBJECT_ID('dbo.portfolio_positions'))
    CREATE INDEX idx_position_ticker ON dbo.portfolio_positions(ticker)
"""
