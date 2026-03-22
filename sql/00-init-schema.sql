-- Auto-generated PostgreSQL initialization schema for img-batch-agent
-- Generated from SQLAlchemy models; safe to re-run.

-- TABLE: announcements

CREATE TABLE IF NOT EXISTS announcements (
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	priority VARCHAR(20), 
	announcement_type VARCHAR(50), 
	is_pinned BOOLEAN, 
	is_published BOOLEAN, 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	cover_image_url VARCHAR(500), 
	cover_image_path VARCHAR(500), 
	target_audience VARCHAR(50), 
	view_count INTEGER, 
	click_count INTEGER, 
	created_by VARCHAR(100), 
	updated_by VARCHAR(100), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_announcements_expires_at ON announcements (expires_at);
CREATE INDEX IF NOT EXISTS ix_announcements_is_pinned ON announcements (is_pinned);
CREATE INDEX IF NOT EXISTS ix_announcements_is_published ON announcements (is_published);
CREATE INDEX IF NOT EXISTS ix_announcements_priority ON announcements (priority);
CREATE INDEX IF NOT EXISTS ix_announcements_priority_pinned ON announcements (priority, is_pinned);
CREATE INDEX IF NOT EXISTS ix_announcements_published_expires ON announcements (is_published, expires_at);

-- TABLE: async_tasks

CREATE TABLE IF NOT EXISTS async_tasks (
	id VARCHAR(36) NOT NULL, 
	platform_task_id VARCHAR(200), 
	task_type VARCHAR(50), 
	platform VARCHAR(50), 
	model VARCHAR(100), 
	prompt TEXT, 
	params JSON, 
	status VARCHAR(50), 
	progress FLOAT, 
	result_urls JSON, 
	error TEXT, 
	submit_time TIMESTAMP WITHOUT TIME ZONE, 
	start_time TIMESTAMP WITHOUT TIME ZONE, 
	end_time TIMESTAMP WITHOUT TIME ZONE, 
	task_metadata JSON, 
	user_id VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_async_tasks_platform ON async_tasks (platform);
CREATE INDEX IF NOT EXISTS ix_async_tasks_platform_task_id ON async_tasks (platform_task_id);
CREATE INDEX IF NOT EXISTS ix_async_tasks_status ON async_tasks (status);
CREATE INDEX IF NOT EXISTS ix_async_tasks_user_id ON async_tasks (user_id);

-- TABLE: billing_plans

CREATE TABLE IF NOT EXISTS billing_plans (
	plan_id VARCHAR(50) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	price INTEGER NOT NULL, 
	original_price INTEGER, 
	duration_days INTEGER, 
	points_included INTEGER, 
	generation_quota INTEGER, 
	daily_quota INTEGER, 
	features JSON, 
	is_active BOOLEAN, 
	sort_order INTEGER, 
	badge_text VARCHAR(50), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (plan_id)
);

-- TABLE: cases

CREATE TABLE IF NOT EXISTS cases (
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	category VARCHAR(50) NOT NULL, 
	tags JSON, 
	thumbnail_url VARCHAR(500), 
	image_url VARCHAR(500), 
	image_path VARCHAR(500), 
	prompt TEXT NOT NULL, 
	negative_prompt TEXT, 
	parameters JSON, 
	provider VARCHAR(100), 
	model VARCHAR(100), 
	is_published BOOLEAN, 
	sort_order INTEGER, 
	view_count INTEGER, 
	use_count INTEGER, 
	created_by VARCHAR(100), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_cases_category ON cases (category);
CREATE INDEX IF NOT EXISTS ix_cases_is_published ON cases (is_published);
CREATE INDEX IF NOT EXISTS ix_cases_sort_order ON cases (sort_order);

-- TABLE: cleanup_history

CREATE TABLE IF NOT EXISTS cleanup_history (
	retention_days INTEGER, 
	cutoff_date TIMESTAMP WITHOUT TIME ZONE, 
	dry_run BOOLEAN, 
	total_image_records_deleted INTEGER, 
	total_chat_records_deleted INTEGER, 
	total_user_requests_deleted INTEGER, 
	total_image_files_deleted INTEGER, 
	total_storage_freed_bytes BIGINT, 
	error_count INTEGER, 
	errors JSON, 
	failed_image_deletions JSON, 
	triggered_by VARCHAR(100), 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	duration_seconds FLOAT, 
	status VARCHAR(20), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

-- TABLE: conversation_sessions

CREATE TABLE IF NOT EXISTS conversation_sessions (
	session_id VARCHAR(100) NOT NULL, 
	client_id VARCHAR(100), 
	title VARCHAR(200), 
	model VARCHAR(100), 
	provider VARCHAR(100), 
	status VARCHAR(20), 
	message_count INTEGER, 
	image_count INTEGER, 
	file_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_conversation_sessions_client_id ON conversation_sessions (client_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_conversation_sessions_session_id ON conversation_sessions (session_id);

-- TABLE: stored_credentials

CREATE TABLE IF NOT EXISTS stored_credentials (
	provider VARCHAR(50) NOT NULL, 
	base_url VARCHAR(500), 
	user_id VARCHAR(100), 
	session_id VARCHAR(100), 
	encrypted_api_key TEXT NOT NULL, 
	key_hint VARCHAR(32), 
	status VARCHAR(20), 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	last_used_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_stored_credentials_provider ON stored_credentials (provider);
CREATE INDEX IF NOT EXISTS ix_stored_credentials_session_id ON stored_credentials (session_id);
CREATE INDEX IF NOT EXISTS ix_stored_credentials_status ON stored_credentials (status);
CREATE INDEX IF NOT EXISTS ix_stored_credentials_user_id ON stored_credentials (user_id);

-- TABLE: system_configs

CREATE TABLE IF NOT EXISTS system_configs (
	config_key VARCHAR(100) NOT NULL, 
	config_value TEXT, 
	config_type VARCHAR(50), 
	category VARCHAR(50), 
	description TEXT, 
	is_encrypted BOOLEAN, 
	is_public BOOLEAN, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_by VARCHAR(100), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_system_configs_config_key ON system_configs (config_key);

-- TABLE: uploaded_files

CREATE TABLE IF NOT EXISTS uploaded_files (
	original_filename VARCHAR(255), 
	stored_filename VARCHAR(255), 
	file_path VARCHAR(500), 
	file_url VARCHAR(500), 
	file_size INTEGER, 
	file_type VARCHAR(100), 
	file_extension VARCHAR(20), 
	category VARCHAR(50), 
	conversation_id VARCHAR(100), 
	message_id INTEGER, 
	is_public BOOLEAN, 
	status VARCHAR(50), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (stored_filename)
);

CREATE INDEX IF NOT EXISTS ix_uploaded_files_conversation_id ON uploaded_files (conversation_id);
CREATE INDEX IF NOT EXISTS ix_uploaded_files_message_id ON uploaded_files (message_id);

-- TABLE: user_requests

CREATE TABLE IF NOT EXISTS user_requests (
	user_id VARCHAR(100), 
	user_ip VARCHAR(50), 
	user_agent VARCHAR(500), 
	request_type VARCHAR(50), 
	request_data JSON, 
	status VARCHAR(50), 
	error_message TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_user_requests_request_type ON user_requests (request_type);
CREATE INDEX IF NOT EXISTS ix_user_requests_user_id ON user_requests (user_id);

-- TABLE: users

CREATE TABLE IF NOT EXISTS users (
	username VARCHAR(50) NOT NULL, 
	phone VARCHAR(20), 
	password_hash VARCHAR(255) NOT NULL, 
	status VARCHAR(20), 
	role VARCHAR(20), 
	last_login_at TIMESTAMP WITHOUT TIME ZONE, 
	last_login_ip VARCHAR(50), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (phone)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);

-- TABLE: accounts

CREATE TABLE IF NOT EXISTS accounts (
	user_id VARCHAR(100) NOT NULL, 
	balance INTEGER, 
	points INTEGER, 
	subscription_plan VARCHAR(50), 
	subscription_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	total_generated INTEGER, 
	total_spent INTEGER, 
	total_points_earned INTEGER, 
	free_quota_used INTEGER, 
	subscription_quota_used INTEGER, 
	gift_points INTEGER, 
	gift_points_expiry TIMESTAMP WITHOUT TIME ZONE, 
	last_checkin_date DATE, 
	consecutive_checkin_days INTEGER, 
	invite_code VARCHAR(20), 
	inviter_id VARCHAR(100), 
	total_invite_count INTEGER, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (invite_code), 
	FOREIGN KEY(inviter_id) REFERENCES users (id)
);

-- TABLE: chat_messages

CREATE TABLE IF NOT EXISTS chat_messages (
	user_request_id VARCHAR(36), 
	session_id VARCHAR(100) NOT NULL, 
	role VARCHAR(50), 
	content TEXT, 
	model VARCHAR(100), 
	provider VARCHAR(100), 
	prompt_tokens INTEGER, 
	completion_tokens INTEGER, 
	total_tokens INTEGER, 
	temperature FLOAT, 
	max_tokens INTEGER, 
	top_p FLOAT, 
	images TEXT, 
	files TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_request_id) REFERENCES user_requests (id), 
	FOREIGN KEY(session_id) REFERENCES conversation_sessions (session_id)
);

-- TABLE: consumption_records

CREATE TABLE IF NOT EXISTS consumption_records (
	user_id VARCHAR(100) NOT NULL, 
	request_id VARCHAR(100), 
	model_name VARCHAR(100), 
	provider VARCHAR(50), 
	cost_type VARCHAR(20) NOT NULL, 
	points_used INTEGER, 
	amount INTEGER, 
	prompt TEXT, 
	image_count INTEGER, 
	image_urls JSON, 
	status VARCHAR(20), 
	error_reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_consumption_records_user_id ON consumption_records (user_id);

-- TABLE: image_generation_records

CREATE TABLE IF NOT EXISTS image_generation_records (
	user_request_id VARCHAR(36) NOT NULL, 
	provider VARCHAR(100), 
	model VARCHAR(100), 
	prompt TEXT, 
	negative_prompt TEXT, 
	width INTEGER, 
	height INTEGER, 
	n INTEGER, 
	style VARCHAR(50), 
	quality VARCHAR(50), 
	extra_params JSON, 
	status VARCHAR(50), 
	image_urls JSON, 
	image_paths JSON, 
	processing_time FLOAT, 
	start_time TIMESTAMP WITHOUT TIME ZONE, 
	end_time TIMESTAMP WITHOUT TIME ZONE, 
	prompt_tokens INTEGER, 
	completion_tokens INTEGER, 
	total_tokens INTEGER, 
	call_mode VARCHAR(50), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_request_id) REFERENCES user_requests (id)
);

-- TABLE: login_logs

CREATE TABLE IF NOT EXISTS login_logs (
	user_id VARCHAR(100), 
	login_type VARCHAR(20), 
	login_ip VARCHAR(50), 
	login_location VARCHAR(100), 
	user_agent VARCHAR(500), 
	status VARCHAR(20), 
	fail_reason VARCHAR(255), 
	logout_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- TABLE: payment_orders

CREATE TABLE IF NOT EXISTS payment_orders (
	order_id VARCHAR(100) NOT NULL, 
	user_id VARCHAR(100) NOT NULL, 
	order_type VARCHAR(20) NOT NULL, 
	amount INTEGER NOT NULL, 
	plan_id VARCHAR(50), 
	payment_method VARCHAR(20) NOT NULL, 
	payment_channel VARCHAR(50), 
	status VARCHAR(20), 
	transaction_id VARCHAR(100), 
	prepay_id VARCHAR(100), 
	qr_code_url TEXT, 
	pay_url TEXT, 
	notify_time TIMESTAMP WITHOUT TIME ZONE, 
	notify_data JSON, 
	expire_time TIMESTAMP WITHOUT TIME ZONE, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	subject VARCHAR(255), 
	body TEXT, 
	attach JSON, 
	client_ip VARCHAR(50), 
	user_agent VARCHAR(500), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_payment_orders_user_id ON payment_orders (user_id);

-- TABLE: system_logs

CREATE TABLE IF NOT EXISTS system_logs (
	level VARCHAR(20), 
	module VARCHAR(100), 
	function VARCHAR(100), 
	message TEXT, 
	details JSON, 
	user_id VARCHAR(100), 
	request_id VARCHAR(36), 
	exception_type VARCHAR(100), 
	exception_message TEXT, 
	traceback TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES user_requests (id)
);

CREATE INDEX IF NOT EXISTS ix_system_logs_level ON system_logs (level);
CREATE INDEX IF NOT EXISTS ix_system_logs_module ON system_logs (module);
CREATE INDEX IF NOT EXISTS ix_system_logs_user_id ON system_logs (user_id);

-- TABLE: transactions

CREATE TABLE IF NOT EXISTS transactions (
	user_id VARCHAR(100) NOT NULL, 
	transaction_type VARCHAR(50) NOT NULL, 
	amount INTEGER, 
	points_change INTEGER, 
	balance_after INTEGER, 
	points_after INTEGER, 
	related_order_id VARCHAR(100), 
	related_request_id VARCHAR(100), 
	description VARCHAR(255), 
	status VARCHAR(20), 
	extra_data JSON, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions (user_id);

-- TABLE: user_auth

CREATE TABLE IF NOT EXISTS user_auth (
	user_id VARCHAR(100) NOT NULL, 
	auth_type VARCHAR(20) NOT NULL, 
	auth_identifier VARCHAR(255) NOT NULL, 
	verified BOOLEAN, 
	verify_code VARCHAR(10), 
	verify_code_expiry TIMESTAMP WITHOUT TIME ZONE, 
	oauth_provider VARCHAR(50), 
	oauth_openid VARCHAR(255), 
	oauth_unionid VARCHAR(255), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_user_auth_type_identifier ON user_auth (auth_type, auth_identifier);

-- TABLE: user_notifications

CREATE TABLE IF NOT EXISTS user_notifications (
	announcement_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(100) NOT NULL, 
	is_read BOOLEAN, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	is_clicked BOOLEAN, 
	clicked_at TIMESTAMP WITHOUT TIME ZONE, 
	is_pushed BOOLEAN, 
	pushed_at TIMESTAMP WITHOUT TIME ZONE, 
	push_method VARCHAR(20), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT unique_user_announcement UNIQUE (announcement_id, user_id), 
	FOREIGN KEY(announcement_id) REFERENCES announcements (id)
);

CREATE INDEX IF NOT EXISTS ix_user_notifications_announcement_id ON user_notifications (announcement_id);
CREATE INDEX IF NOT EXISTS ix_user_notifications_announcement_read ON user_notifications (announcement_id, is_read);
CREATE INDEX IF NOT EXISTS ix_user_notifications_is_read ON user_notifications (is_read);
CREATE INDEX IF NOT EXISTS ix_user_notifications_user_id ON user_notifications (user_id);
CREATE INDEX IF NOT EXISTS ix_user_notifications_user_read ON user_notifications (user_id, is_read);

-- TABLE: withdrawals

CREATE TABLE IF NOT EXISTS withdrawals (
	withdrawal_id VARCHAR(100) NOT NULL, 
	user_id VARCHAR(100) NOT NULL, 
	amount INTEGER NOT NULL, 
	withdrawal_method VARCHAR(20) NOT NULL, 
	withdrawal_account VARCHAR(200), 
	withdrawal_name VARCHAR(100), 
	status VARCHAR(20), 
	admin_id VARCHAR(100), 
	review_note VARCHAR(500), 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	payment_proof VARCHAR(500), 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	user_note VARCHAR(500), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (withdrawal_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_withdrawals_user_id ON withdrawals (user_id);

-- TABLE: download_records

CREATE TABLE IF NOT EXISTS download_records (
	user_id VARCHAR(100) NOT NULL, 
	image_url TEXT, 
	file_name VARCHAR(255), 
	file_size INTEGER, 
	request_id VARCHAR(100), 
	consumption_record_id VARCHAR(100), 
	download_ip VARCHAR(50), 
	user_agent VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(consumption_record_id) REFERENCES consumption_records (id)
);

CREATE INDEX IF NOT EXISTS ix_download_records_user_id ON download_records (user_id);

-- TABLE: payment_refunds

CREATE TABLE IF NOT EXISTS payment_refunds (
	payment_order_id VARCHAR(100) NOT NULL, 
	refund_id VARCHAR(100) NOT NULL, 
	refund_amount INTEGER NOT NULL, 
	refund_reason VARCHAR(255), 
	status VARCHAR(20), 
	refund_transaction_id VARCHAR(100), 
	refund_time TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(payment_order_id) REFERENCES payment_orders (order_id), 
	UNIQUE (refund_id)
);
