# Stage 1: Clone required repositories and prepare addons
FROM alpine/git AS build

# Create working directories
RUN mkdir -p /mnt/repositories /mnt/extra-addons
WORKDIR /mnt/repositories

# Clone only required repos shallowly
RUN git clone --depth 1 https://github.com/OCA/social \
 && git clone --depth 1 https://github.com/OCA/helpdesk

# Move selected addons
RUN mv \
    social/mail_gateway \
    helpdesk/helpdesk_mgmt \
    /mnt/extra-addons/

# Clean up repositories to reduce image size
RUN rm -rf /mnt/repositories

# Stage 2: Final image based on official Odoo
FROM odoo:18

# Environment setup
ENV ODOO_USER=odoo \
    ADDONS_DIR=/mnt/extra-addons

# Create and copy custom addons
RUN mkdir -p ${ADDONS_DIR}
COPY --from=build /mnt/extra-addons/ ${ADDONS_DIR}/
COPY mail_discuss_hub ${ADDONS_DIR}/mail_discuss_hub
COPY mail_discuss_hub_crm ${ADDONS_DIR}/mail_discuss_hub_crm
COPY mail_discuss_hub_gateway ${ADDONS_DIR}/mail_discuss_hub_gateway
COPY mail_discuss_hub_gateway_devtools ${ADDONS_DIR}/mail_discuss_hub_gateway_devtools
COPY mail_discuss_hub_helpdesk_mgmt ${ADDONS_DIR}/mail_discuss_hub_helpdesk_mgmt
COPY mail_gateway_whatsapp_common ${ADDONS_DIR}/mail_gateway_whatsapp_common
COPY mail_gateway_whatsapp_evolution_api ${ADDONS_DIR}/mail_gateway_whatsapp_evolution_api
COPY mail_gateway_whatsapp_evolution_api_chatwoot ${ADDONS_DIR}/mail_gateway_whatsapp_evolution_api_chatwoot
COPY mail_gateway_whatsapp_evolution_api_manager ${ADDONS_DIR}/mail_gateway_whatsapp_evolution_api_manager
COPY mail_gateway_whatsapp_waha ${ADDONS_DIR}/mail_gateway_whatsapp_waha

# Install Python dependencies

USER root
RUN chown -R ${ODOO_USER}:${ODOO_USER} ${ADDONS_DIR} \
 && pip3 install --no-cache-dir --break-system-packages redis python-json-logger statsd boto

USER ${ODOO_USER}

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]