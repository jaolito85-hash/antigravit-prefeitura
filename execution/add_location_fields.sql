-- Migração: adiciona campos de endereço e status de localização
-- Seguro para rodar múltiplas vezes (IF NOT EXISTS)

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS rua TEXT;
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS location_status TEXT DEFAULT 'pendente';

-- Backfill: registros que já têm região conhecida consideram localização suficiente
UPDATE feedbacks
SET location_status = 'completo'
WHERE location_status IS NULL OR location_status = 'pendente'
  AND region IS NOT NULL AND region != 'N/A';
