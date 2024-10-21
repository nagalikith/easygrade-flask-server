import sqlalchemy as sa
from sqlalchemy.sql import func
import import_helper as ih

id_size = ih.get_env_val("HEX_ID_LENGTH")
url_size = 150

metadata = sa.MetaData()

def reg_schema():
    # Create ENUM types first
    # Note: Using VARCHAR instead of ENUM for better flexibility and avoiding migration issues
    USER_ROLES = ['student', 'instructor', 'admin']
    ASSIGNMENT_TYPES = ['homework', 'quiz', 'exam', 'project']

    def audit_columns():
        return [
            sa.Column("created_at", sa.DateTime, server_default=func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
            sa.Column("is_active", sa.Boolean, server_default='true', nullable=False)
        ]

    # User management tables
    user_info = sa.Table("user_info", metadata,
        sa.Column("user_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("username", sa.Unicode(32), unique=True, index=True),
        sa.Column("hashed_password", sa.Unicode(90), nullable=False),
        sa.Column("email", sa.Unicode(100), unique=True, index=True),
        sa.Column("reg_epoch", sa.Float(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # Using String instead of Enum
        sa.Column("last_login", sa.DateTime),
        sa.Column("failed_login_attempts", sa.Integer, default=0),
        sa.Column("account_locked_until", sa.DateTime),
        *audit_columns(),
        sa.CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name="valid_email"),
        sa.CheckConstraint(f"role IN {tuple(USER_ROLES)}", name="valid_role")
    )

    # New table for course roster
    course_roster = sa.Table("course_roster", metadata,
        sa.Column("roster_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("section_id", sa.ForeignKey("section.section_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # Using String instead of Enum
        *audit_columns(),
        sa.CheckConstraint(f"role IN {tuple(USER_ROLES)}", name="valid_course_role")
    )

    # New table for user preferences
    user_preferences = sa.Table("user_preferences", metadata,
        sa.Column("preference_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("preference_type", sa.String(50), nullable=False),  # e.g., "course_order" or "assignment_order"
        sa.Column("preference_value", sa.JSON, nullable=False),  # JSON to store order of courses or assignments
        *audit_columns()
    )

    user_auth = sa.Table("user_auth", metadata,
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("eph_pass", sa.Unicode(id_size), nullable=False),
        sa.Column("last_access", sa.Float(), nullable=False),
        sa.Column("period_start", sa.Float(), nullable=False),
        sa.Column("num_hits", sa.Integer(), nullable=False),
        sa.Column("token_expiry", sa.DateTime, nullable=False),
        *audit_columns(),
        sa.CheckConstraint("num_hits >= 0", name="valid_hits_count")
    )

    # Audit trail table
    audit_log = sa.Table("audit_log", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("table_name", sa.String(50), nullable=False),
        sa.Column("record_id", sa.Unicode(id_size), nullable=False),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("old_values", sa.JSON),
        sa.Column("new_values", sa.JSON),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id")),
        sa.Column("timestamp", sa.DateTime, server_default=func.now())
    )

    section = sa.Table("section", metadata,
        sa.Column("section_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("section_code", sa.Unicode(32), index=True, nullable=False),
        sa.Column("section_name", sa.Unicode(100)),
        sa.Column("academic_year", sa.Integer, nullable=False),
        sa.Column("semester", sa.String(20), nullable=False),
        *audit_columns(),
        sa.UniqueConstraint('section_code', 'academic_year', 'semester', name='unique_section_period')
    )

    sec_acc = sa.Table("sec_acc", metadata,
        sa.Column("section_id", sa.ForeignKey("section.section_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(20), nullable=False),  # Using String instead of Enum
        sa.Column("add_epoch", sa.Float(), nullable=False),
        *audit_columns(),
        sa.CheckConstraint(f"role IN {tuple(USER_ROLES)}", name="valid_sec_role")
    )

    assn = sa.Table("assn", metadata,
        sa.Column("assn_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("author_id", sa.ForeignKey("user_info.user_id"), index=True, nullable=False),
        sa.Column("assn_title", sa.Unicode(50), nullable=False),
        sa.Column("assn_body", sa.Unicode(100), nullable=False),
        sa.Column("assn_type", sa.String(20), nullable=False),  # Using String instead of Enum
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("last_upd", sa.Float(), nullable=False),
        sa.Column("start_epoch", sa.Float(), nullable=False),
        sa.Column("end_epoch", sa.Float(), nullable=False),
        sa.Column("assn_url", sa.Unicode(url_size), nullable=False),
        sa.Column("max_attempts", sa.Integer),
        *audit_columns(),
        sa.CheckConstraint('end_epoch > start_epoch', name='valid_date_range'),
        sa.CheckConstraint('max_score >= 0', name='valid_max_score'),
        sa.CheckConstraint('weight >= 0', name='valid_weight'),
        sa.CheckConstraint(f"assn_type IN {tuple(ASSIGNMENT_TYPES)}", name="valid_assn_type")
    )

    assn_acc = sa.Table("assn_acc", metadata,
        sa.Column("assn_id", sa.ForeignKey("assn.assn_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("section_id", sa.ForeignKey("section.section_id", ondelete="CASCADE"), index=True, nullable=False),
        *audit_columns()
    )

    subm = sa.Table("subm", metadata,
        sa.Column("subm_id", sa.Unicode(id_size), primary_key=True),
        sa.Column("upload_epoch", sa.Float(), nullable=False),
        sa.Column("subm_url", sa.Unicode(url_size), nullable=False),
        sa.Column("assn_id", sa.ForeignKey("assn.assn_id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("grader_id", sa.ForeignKey("user_info.user_id"), nullable=True),
        sa.Column("feedback", sa.Text),
        *audit_columns(),
        sa.CheckConstraint('score >= 0', name='valid_score')
    )

    subm_aggr = sa.Table("subm_aggr", metadata,
        sa.Column("assn_id", sa.ForeignKey("assn.assn_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.ForeignKey("user_info.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("best_subm_id", sa.ForeignKey("subm.subm_id", ondelete="CASCADE"), nullable=False),
        sa.Column("num_attempts", sa.Integer(), default=0, nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        *audit_columns(),
        sa.CheckConstraint('num_attempts >= 0', name='valid_attempts'),
        sa.CheckConstraint('final_score >= 0', name='valid_final_score')
    )

    # Create indexes
    sa.Index('idx_submission_user_assn', subm.c.user_id, subm.c.assn_id)
    sa.Index('idx_assn_date_range', assn.c.start_epoch, assn.c.end_epoch)
    sa.Index('idx_user_section', sec_acc.c.user_id, sec_acc.c.section_id)
    sa.Index('idx_course_roster_section_user', course_roster.c.section_id, course_roster.c.user_id)
    sa.Index('idx_user_preferences_user_type', user_preferences.c.user_id, user_preferences.c.preference_type)

    reg_schema()

# Dictionary to store table information
tables_info = {}
for tb_name in metadata.tables:
    tables_info[tb_name] = {"table": metadata.tables[tb_name], "col":{}}
    for col in metadata.tables[tb_name].c:
        tables_info[tb_name]["col"][col.name] = col