# Comment System Demo

This project demonstrates a fully functional comment system integrated into a Reflex web application.

## Features

- **Real-time Comments**: View and post comments with live updates
- **User Roles**: Different permissions for MEMBERS, SUPERVISORS, and USERS
- **Responsive Design**: Clean, modern UI with avatars and role badges
- **Error Handling**: Graceful error handling with user-friendly messages
- **Loading States**: Visual feedback during API calls

## Quick Start

### 1. Install Dependencies

```bash
pip install reflex fastapi uvicorn httpx
```

### 2. Start the Mock API Server

Open a terminal and run:

```bash
python mock_api.py
```

This will start a mock API server on `http://localhost:8000` that provides sample comments.

### 3. Start the Reflex App

In another terminal, run:

```bash
reflex run
```

The app will be available at `http://localhost:3000`

## How It Works

### Comment Component (`AddOnStuffs/comment.py`)

The comment system consists of:

1. **CommentState**: Manages comment data, user permissions, and API interactions
2. **comment_section()**: Main UI component that renders the entire comment interface
3. **Mock API**: FastAPI server that simulates a backend for demo purposes

### Key Features

- **Role-based Access**: Only MEMBERS and SUPERVISORS can post comments
- **Live Updates**: Comments appear immediately after posting
- **User Avatars**: Color-coded avatars based on user role (yellow for SUPERVISOR, blue for MEMBER)
- **Timestamps**: Each comment shows when it was created
- **Error Recovery**: Failed operations show helpful error messages

### Integration

The comment system is integrated into the main app in `ProjCode/ProjCode.py`:

```python
from AddOnStuffs.comment import CommentState, comment_section

# In the page component:
rx.box(
    comment_section(),
    on_mount=CommentState.load_comments(1),  # Load comments for task_id=1
)
```

## Customization

### Changing User Role

Edit the `current_user_role` in `AddOnStuffs/comment.py`:

```python
current_user_role: str = "SUPERVISOR"  # Try "MEMBER" or "USER"
```

### Adding Sample Comments

Modify the `mock_comments` dictionary in `mock_api.py` to add more sample data.

### Styling

The UI uses Reflex's built-in styling system. You can customize colors, sizes, and layouts by modifying the component properties in `comment.py`.

## Production Usage

For production use:

1. Replace the mock API with your real backend
2. Set `API_BASE` to your production API URL
3. Integrate with your authentication system to set `current_user_*` values
4. Add proper error handling and validation

## File Structure

```
ProjCode/
├── AddOnStuffs/
│   └── comment.py          # Comment system components
├── ProjCode/
│   └── ProjCode.py        # Main Reflex app
├── mock_api.py            # Mock API server for demo
└── README.md              # This file
```