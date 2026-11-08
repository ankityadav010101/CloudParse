# NACL design notes

The NACL is stateless: it does not remember that an inbound connection was allowed. A reply from the application subnet therefore needs its own outbound ephemeral-port rule. Client replies arriving at the public load balancer also need an inbound ephemeral-port rule. The allow range is 1024-65535, matching the assignment's client-port assumption.

The abusive 198.51.100.0/24 deny is rule 90, before broad HTTP/HTTPS allows. If the deny were numbered after those allows, first-match evaluation would already have accepted matching web traffic and never reach the deny. SSH is limited to the management subnet. Outbound application traffic permits only TCP 8000 to the app subnet and ephemeral replies to clients; unmatched traffic follows default deny.
