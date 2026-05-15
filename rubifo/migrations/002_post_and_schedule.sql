-- M3: Schema for routes and post_queue

CREATE TABLE IF NOT EXISTS routes (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_channel_id BIGINT NOT NULL,
  target_channel_id BIGINT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routes_user_id ON routes(user_id);
CREATE INDEX IF NOT EXISTS idx_routes_source_target ON routes(source_channel_id, target_channel_id);

CREATE TABLE IF NOT EXISTS post_queue (
  id SERIAL PRIMARY KEY,
  route_id BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  message_id_in_source BIGINT NOT NULL,
  source_date TIMESTAMP NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  retry_count INTEGER DEFAULT 0,
  last_error TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_queue_route_id ON post_queue(route_id);
CREATE INDEX IF NOT EXISTS idx_post_queue_status ON post_queue(status);
CREATE INDEX IF NOT EXISTS idx_post_queue_source_date ON post_queue(source_date);
