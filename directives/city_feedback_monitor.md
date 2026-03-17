# Directive: Handle City Feedback Reports

## Goal

Receive WhatsApp messages from citizens about municipal services, acknowledge them immediately, classify and log them for the dashboard.

## Triggers

- Incoming Webhook from Evolution API (type: `messages.upsert`)

## Steps

1. **Validation**: Ensure message is not from the bot itself (`key.fromMe` should be false).
2. **Extraction**:
   - `remoteJid`: The citizen's phone number.
   - `pushName`: Citizen's name.
   - `text`: The content of the report (e.g., "Buraco na rua tal").
3. **Classification** (deterministic keywords first, AI fallback):
   - **Categoria**: Infraestrutura & Obras, Saúde & Atendimento, Educação & Escolas, Segurança Pública, Limpeza & Meio Ambiente, Transporte & Mobilidade
   - **Sentimento**: Positivo, Neutro, Urgente, Critico
   - **Região**: Centro, Zona Norte, Zona Sul, Zona Leste, Zona Oeste, Distrito Industrial, Zona Rural
4. **Action**:
   - **Log**: Save report to Supabase (table: `feedbacks`)
   - **Reply**: Send institutional WhatsApp response confirming receipt

## Edge Cases

- **Media messages**: If user sends photo/audio, reply with: "Por favor, envie apenas texto descrevendo a ocorrência." (Optional for MVP)
- **Duplicate messages**: Hash-based deduplication prevents duplicates
