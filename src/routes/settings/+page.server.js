/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
	try {
		// We assume sensor_id 1 is the primary "Fabritag Device" as seen in firmware.ino
		const sensorId = 1;
		const response = await fetch(`http://127.0.0.1:5000/api/sensor/status/${sensorId}`);

		if (response.ok) {
			const sensorStatus = await response.json();
			return {
				sensorStatus
			};
		}

		// If 404, it means it never pinged
		return {
			sensorStatus: { status: 'Offline', ip_address: 'N/A' }
		};
	} catch (error) {
		console.error('Error fetching sensor status:', error);
		return {
			sensorStatus: { status: 'Offline', ip_address: 'N/A' }
		};
	}
}
