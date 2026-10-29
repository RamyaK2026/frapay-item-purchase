# Ecommerce-Application-
# Frapay – Item & Purchase Management (ERPNext / Frappe)

Assignment submission: Item & Purchase Management System.
Built as a custom app on ERPNext/Frappe with Python and MySQL (MariaDB), instead of Node.js/Express.

## Where things are
- Full README (setup, rules, JOINs, tests): [frapay/README.md](frapay/README.md)
- API documentation: [frapay/API.md](frapay/API.md)
- Postman collection: [frapay/Frapay.postman_collection.json](frapay/Frapay.postman_collection.json)
- Source code: [frapay/frapay](frapay/frapay)
- Screenshots: [screenshots](screenshots)

## Quick install (existing bench)
1. Copy the `frapay` folder from this repo into `<bench>/apps/`
2. `<bench>/env/bin/pip install -e <bench>/apps/frapay`
3. `bench --site <site> install-app frapay`
4. `bench --site <site> migrate`
5. Optional demo data: `bench --site <site> execute frapay.setup.install.load_sample_data`
