/*
 * otopi -- plugable installer
 */
package org.ovirt.otopi.dialog;

/**
 * Dialog event types.
 */
public class Event {
	/**
	 * Base for events.
	 */
	public static class Base {}
	/**
	 * Log
	 */
	public static class Log extends Base {
		/**
		 * Log severity.
		 */
		public enum Severity {
			INFO,
			WARNING,
			ERROR,
			CRITICAL,
			FATAL
		}
		public Severity severity;
		public String record;
		public String toString() {
			return String.format(
				"Log %1$s %2$s",
				severity,
				record
			);
		}
	}
	/**
	 * Query string.
	 */
	public static class QueryString extends Base {
		public String name;
		public String value;
		public String toString() {
			return String.format(
				"QueryString %1$s %2$s",
				name,
				value
			);
		}
	}
	/**
	 * Query multi string.
	 */
	public static class QueryMultiString extends Base {
		public String name;
		public String boundary;
		public String abortboundary;
		public boolean abort = false;
		public String value[];
		public String toString() {
			return String.format(
				"QueryMultiString %1$s %2$s",
				name,
				value == null ? "null" : value.length
			);
		}
	}
	/**
	 * Query value.
	 */
	public static class QueryValue extends Base {
		public String name;
		public boolean abort = false;
		public Object value;
		public String toString() {
			return String.format(
				"QueryValue %1$s=%2$s abort=%3$s",
				name,
				value,
				abort
			);
		}
	}
	/**
	 * Display value.
	 */
	public static class DisplayValue extends Base {
		public String name;
		public String type;
		public Object value;
		public String toString() {
			return String.format(
				"DisplayValue %1$s=%2$s:%3$s",
				name,
				type,
				value
			);
		}
	}
	/**
	 * Display multi string.
	 */
	public static class DisplayMultiString extends Base {
		public String name;
		public String boundary;
		public String value[];
		public String toString() {
			return String.format(
				"DisplayMultiString %1$s %2$s",
				name,
				value == null ? "null" : value.length
			);
		}
	}
	/**
	 * Confirm.
	 */
	public static class Confirm extends Base {
		public String what;
		public String description;
		public boolean abort = false;
		public boolean reply = false;
		public String toString() {
			return String.format(
				"Confirm %1$s(%2$s) abort=%4$s",
				what,
				description,
				reply,
				abort
			);
		}
	}
	/**
	 * Terminate.
	 */
	public static class Terminate extends Base {
		public String toString() {
			return "Terminate";
		}
	}
}
