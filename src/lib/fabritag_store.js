import { writable } from 'svelte/store';

const INITIAL_DATA = {
	produtos: [
		{
			id: 1,
			nome: 'Prego Aço 15x15',
			sku: 'PRE-15-ACO',
			tipo: 'Granel',
			status: 'Armazenado',
			local: 'Câmara 1'
		},
		{
			id: 2,
			nome: 'Parafuso Sextavado',
			sku: 'PAR-SEX-10',
			tipo: 'Unidade',
			status: 'Em Trânsito',
			local: 'Corredor B'
		},
		{
			id: 3,
			nome: 'Porca 10mm',
			sku: 'POR-10-INOX',
			tipo: 'Granel',
			status: 'Armazenado',
			local: 'Câmara 2'
		}
	],
	camaras: [
		{ id: 1, nome: 'Câmara Fria 01', predio: 'Bloco A', temperatura: '-5°C' },
		{ id: 2, nome: 'Câmara Seca 02', predio: 'Bloco B', temperatura: '22°C' },
		{ id: 3, nome: 'Doca de Expedição', predio: 'Bloco C', temperatura: 'Ambiente' }
	],
	sensores: [
		{ id: 1, modelo: 'PN5180', ip: '192.168.1.101', local_id: 1, status: 'Ativo' },
		{ id: 2, modelo: 'PN5180', ip: '192.168.1.102', local_id: 2, status: 'Ativo' },
		{ id: 3, modelo: 'ESP32-CAM', ip: '192.168.1.200', local_id: 3, status: 'Inativo' }
	],
	historico: [
		{
			id: 1,
			produto: 'Prego Aço 15x15',
			origem: 'Produção',
			destino: 'Câmara 1',
			data: '2026-01-02 08:30'
		},
		{
			id: 2,
			produto: 'Parafuso Sextavado',
			origem: 'Câmara 1',
			destino: 'Corredor B',
			data: '2026-01-02 09:15'
		}
	]
};

export const fabritagData = writable(INITIAL_DATA);
