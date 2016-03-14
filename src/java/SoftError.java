/*
 * otopi -- plugable installer
 */
package org.ovirt.otopi.dialog;

/**
 * Runtime excpetion that is within an abortable
 * context.
 */
public class SoftError extends RuntimeException {

	private static final long serialVersionUID = 3075919756796110432L;

	public SoftError(String message) {
		super(message);
	}
	public SoftError(String message, Throwable cause) {
		super(message, cause);
	}
}

