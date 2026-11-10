const publishedSheets = {
  transporte: {
    base: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQpBOuVF4QhZe1_PHMW9I-NVIyQ90EtOnkgl64STbH3tJupebUigPjAlqQp0RlIbBShFSc4VFUhMkCX/pub?output=csv&gid=',
    sheets: [
      { index: 0, gid: '1886662094', name: '% Indicador general operación' },
      { index: 1, gid: '0', name: '% Ontime' },
      { index: 2, gid: '1110150784', name: '% Infull' },
      { index: 7, gid: '1237360999', name: 'Detalle Infull' },
      { index: 3, gid: '374847431', name: '% Efectividad' },
      { index: 4, gid: '2061749740', name: '% Retorno documental' },
      { index: 5, gid: '758399382', name: '% Ocupación vehicular' },
      { index: 6, gid: '1894820028', name: 'Averías / Hurtos' },
    ],
  },
  almacenamiento: {
    base: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQl82isymo-mRMYkh7NCiFo_-eduaG-EomFQhNhNKFstvZtmh0NQf-txlrgUJgor95_SZD78VZvyzmL/pub?output=csv&gid=',
    sheets: [
      { index: 0, gid: '0', name: 'Inventario cíclico' },
      { index: 1, gid: '69258331', name: '% Ocupación bodega día Celta' },
      { index: 2, gid: '754815625', name: 'Cantidad ingresos' },
      { index: 3, gid: '1782333461', name: 'Armado cigarrillo Celta' },
    ],
  },
};

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Método no permitido.' });
  }

  const source = new URL(req.url, 'http://localhost').searchParams.get('source');
  const config = publishedSheets[source];
  if (!config) return res.status(400).json({ error: 'Fuente de datos no reconocida.' });

  try {
    const sheets = await Promise.all(config.sheets.map(async (sheet) => {
      const response = await fetch(config.base + sheet.gid, {
        headers: { 'User-Agent': 'BAT-Dashboard/1.0' },
        signal: AbortSignal.timeout(18000),
      });
      if (!response.ok) throw new Error(`Google Sheets respondió HTTP ${response.status}.`);
      return { ...sheet, csv: await response.text() };
    }));
    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json({ sheets });
  } catch (error) {
    res.setHeader('Cache-Control', 'no-store');
    return res.status(502).json({ error: `No se pudieron consultar las hojas publicadas: ${error.message}` });
  }
};
