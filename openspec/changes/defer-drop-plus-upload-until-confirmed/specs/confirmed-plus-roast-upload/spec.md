## ADDED Requirements

### Requirement: Confirmed completed roast upload boundary
The system SHALL queue the initial artisan.plus upload for a completed roast only from a user-confirmed completed roast properties save.

#### Scenario: Accepted completed roast properties queue upload
- **WHEN** a roast is recording, has CHARGE and DROP indices set, has safe-save changes, is connected to artisan.plus, is not in simulator mode, and the user accepts the roast properties dialog
- **THEN** the system SHALL queue exactly one completed roast upload attempt through the artisan.plus queue

#### Scenario: Canceled completed roast properties do not queue upload
- **WHEN** a roast has DROP set and the user cancels or closes the roast properties dialog without accepting it
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload

#### Scenario: Properties opened to start recording do not queue upload
- **WHEN** the roast properties dialog is accepted only to start recording on exit
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload

### Requirement: DROP remains a local event before confirmation
The system SHALL treat DROP handlers as local roast-state mutations and SHALL NOT queue artisan.plus completed roast uploads directly from DROP actions.

#### Scenario: Manual DROP does not queue upload immediately
- **WHEN** a connected artisan.plus user presses the DROP button during recording
- **THEN** the system SHALL mark the local DROP state and SHALL NOT call the artisan.plus roast upload queue before the roast properties dialog is accepted

#### Scenario: Undo DROP after mistaken DROP does not require remote cleanup
- **WHEN** a connected artisan.plus user presses DROP and then immediately performs Undo DROP before accepting roast properties
- **THEN** the system SHALL NOT have queued an artisan.plus completed roast upload for the mistaken DROP

#### Scenario: Canvas popup DROP placement does not bypass confirmation
- **WHEN** a connected artisan.plus user sets a first DROP marker through the canvas event popup path
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload before the roast properties dialog is accepted

### Requirement: Confirmed upload gate preserves existing exclusions
The system MUST preserve the current exclusions that prevent artisan.plus upload for incomplete or unsupported completed-roast states.

#### Scenario: Simulator mode suppresses upload
- **WHEN** a completed roast properties dialog is accepted while simulator mode is active
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload

#### Scenario: Missing plus account suppresses upload
- **WHEN** a completed roast properties dialog is accepted without an artisan.plus account connected
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload

#### Scenario: Readonly plus account suppresses upload
- **WHEN** a completed roast properties dialog is accepted while the connected artisan.plus account is readonly
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload, register schedule completion, or refresh plus status

#### Scenario: Missing CHARGE or DROP suppresses upload
- **WHEN** a completed roast properties dialog is accepted while CHARGE or DROP is not set
- **THEN** the system SHALL NOT queue an artisan.plus completed roast upload

### Requirement: Confirmed plus completion side effects are atomic
The system SHALL perform artisan.plus schedule completion registration and plus status refresh only as part of the same confirmed completed-roast upload path.

#### Scenario: Schedule completion follows confirmed upload
- **WHEN** a connected artisan.plus user accepts completed roast properties and a schedule window is present
- **THEN** the system SHALL register the completed roast with the schedule window as part of the confirmed upload path

#### Scenario: Status refresh follows confirmed upload
- **WHEN** a connected artisan.plus user accepts completed roast properties and the upload gate passes
- **THEN** the system SHALL refresh plus status as part of the confirmed upload path
