## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import sqlalchemy as sa
import import_helper as ih

id_size = ih.get_env_val("HEX_ID_LENGTH")
url_size = 150

metadata = sa.MetaData()

def reg_schema():
  
  ## user table
  user_info = sa.Table("user_info", metadata,
    sa.Column("user_id", sa.Unicode(id_size), primary_key=True),
    sa.Column("username", sa.Unicode(32), unique=True, index=True),
    sa.Column("hashed_password", sa.Unicode(90), nullable=False),
    sa.Column("email", sa.Unicode(100)),
    sa.Column("reg_epoch", sa.Float(), nullable=False)
  )

  ## user auth table
  user_auth = sa.Table("user_auth", metadata,
    sa.Column("user_id", sa.ForeignKey("user_info.user_id"), primary_key=True),
    sa.Column("eph_pass", sa.Unicode(id_size), nullable=False),
    sa.Column("last_access", sa.Float(), nullable=False),
    sa.Column("period_start", sa.Float(), nullable=False),
    sa.Column("num_hits", sa.Integer(), nullable=False)
  )

  ## section table
  section = sa.Table("section", metadata,
    sa.Column("section_id", sa.Unicode(id_size), primary_key=True),
    sa.Column("section_code", sa.Unicode(32), index=True, nullable=False),
    sa.Column("section_name", sa.Unicode(100))
  )

  ## section access table
  sec_acc = sa.Table("sec_acc", metadata,
    sa.Column("section_id", sa.ForeignKey("section.section_id"), primary_key=True),
    sa.Column("user_id", sa.ForeignKey("user_info.user_id"), primary_key=True),
    sa.Column("role", sa.Unicode(1), nullable=False),
    sa.Column("add_epoch", sa.Float(), nullable=False)
  )

  ## assignment table
  assn = sa.Table("assn", metadata,
    sa.Column("assn_id", sa.Unicode(id_size), primary_key=True),
    sa.Column("author_id", sa.ForeignKey("user_info.user_id"), index=True, nullable=False),
    sa.Column("assn_title", sa.Unicode(50), nullable=False),
    sa.Column("assn_body", sa.Unicode(100), nullable=False),
    sa.Column("last_upd", sa.Float(), nullable=False),
    sa.Column("start_epoch", sa.Float(), nullable=False),
    sa.Column("end_epoch", sa.Float(), nullable=False),
    sa.Column("assn_url", sa.Unicode(url_size), nullable=False)
  )

  #assignment access table
  assn_acc = sa.Table("assn_acc", metadata,
    sa.Column("assn_id", sa.ForeignKey("assn.assn_id"), primary_key=True),
    sa.Column("user_id", sa.ForeignKey("user_info.user_id"), primary_key=True),
    sa.Column("section_id", sa.ForeignKey("section.section_id"), index=True, nullable=False),
  )

  #submission table
  subm = sa.Table("subm", metadata,
    sa.Column("subm_id", sa.Unicode(id_size), primary_key=True),
    sa.Column("upload_epoch", sa.Float(), nullable=False),
    sa.Column("subm_url", sa.Unicode(url_size), nullable=False),
    sa.Column("assn_id", sa.ForeignKey("assn.assn_id"), index=True, nullable=False),
    sa.Column("user_id", sa.ForeignKey("user_info.user_id"), index=True, nullable=False),
    sa.Column("score", sa.Float(), nullable=False)
  )

  #submission aggregate table for an assignment
  subm_aggr = sa.Table("subm_aggr", metadata,
    sa.Column("assn_id", sa.ForeignKey("assn.assn_id"), primary_key=True),
    sa.Column("user_id", sa.ForeignKey("user_info.user_id"), primary_key=True),
    sa.Column("best_subm_id", sa.ForeignKey("subm.subm_id"), nullable=False),
    sa.Column("num_attempts", sa.Integer(), default=0, nullable=False)
  )

reg_schema()
tables_info = {}

for tb_name in metadata.tables:
  tables_info[tb_name] = {"table": metadata.tables[tb_name], "col":{}}
  for col in metadata.tables[tb_name].c:
    tables_info[tb_name]["col"][col.name] = col

## EOF
