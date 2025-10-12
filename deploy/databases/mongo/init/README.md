# MongoDB Initialisation Scripts

Drop JavaScript files into this directory to seed collections, indexes and
users. The MongoDB container runs each script during bootstrap using the root
credentials defined in the compose file. Keep seed data idempotent to support
re-deployments.
