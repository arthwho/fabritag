/**
 * A shared state for sensor statuses.
 * This can be imported into any component to get real-time status.
 */
class SensorStore {
	#statuses = $state({});
	#isPolling = false;

	constructor() {}

	/**
	 * Returns the current statuses.
	 */
	get liveStatuses() {
		return this.#statuses;
	}

	/**
	 * Returns the count of sensors that are Online.
	 */
	get onlineCount() {
		return Object.values(this.#statuses).filter((s) => s.status === 'Online').length;
	}

	/**
	 * Sets the initial statuses, e.g., from server-side data.
	 * @param {Record<string, any>} initialStatuses
	 */
	setInitial(initialStatuses) {
		if (initialStatuses) {
			this.#statuses = initialStatuses;
		}
	}

	/**
	 * Starts polling the sensor status API.
	 * Call this in onMount if you want the global state to refresh.
	 */
	startPolling(intervalMs = 15000) {
		if (this.#isPolling) return () => {};
		this.#isPolling = true;

		const poll = async () => {
			try {
				const response = await fetch('http://127.0.0.1:5000/api/dispositivos/status');
				if (response.ok) {
					this.#statuses = await response.json();
				}
			} catch (err) {
				console.error('Error polling sensors:', err);
			}
		};

		poll();
		const interval = setInterval(poll, intervalMs);

		return () => {
			clearInterval(interval);
			this.#isPolling = false;
		};
	}
}

export const sensorStore = new SensorStore();
