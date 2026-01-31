package models

import (
	"time"
)

// Enums (represented as strings in Go/DB)
type UserRole string

const (
	RoleOwner  UserRole = "OWNER"
	RoleAdmin  UserRole = "ADMIN"
	RoleMember UserRole = "MEMBER"
	RoleViewer UserRole = "VIEWER"
)

type SubscriptionTier string

const (
	TierFree       SubscriptionTier = "FREE"
	TierPro        SubscriptionTier = "PRO"
	TierEnterprise SubscriptionTier = "ENTERPRISE"
)

// --- Models ---

type User struct {
	ID          string     `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"` // SQLite/Postgres compatible UUID
	FirebaseUID string     `gorm:"uniqueIndex;not null" json:"firebase_uid"`
	Email       string     `gorm:"uniqueIndex;not null" json:"email"`
	FullName    string     `json:"full_name"`
	AvatarURL   string     `json:"avatar_url"`
	IsActive    bool       `gorm:"default:true" json:"is_active"`
	CreatedAt   time.Time  `gorm:"autoCreateTime" json:"created_at"`
	LastLoginAt *time.Time `json:"last_login_at"`

	// Relationships
	Memberships   []OrganizationMember `gorm:"foreignKey:UserID" json:"memberships,omitempty"`
	AuditLogs     []AuditLog           `gorm:"foreignKey:UserID" json:"audit_logs,omitempty"`
	Conversations []Conversation       `gorm:"foreignKey:UserID" json:"conversations,omitempty"`
}

type Organization struct {
	ID               string           `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"`
	Name             string           `gorm:"not null" json:"name"`
	Domain           string           `gorm:"index" json:"domain"`
	SubscriptionTier SubscriptionTier `gorm:"default:'FREE'" json:"subscription_tier"`
	MaxSeats         int              `gorm:"default:5" json:"max_seats"`
	CreatedAt        time.Time        `gorm:"autoCreateTime" json:"created_at"`

	// Relationships
	Members []OrganizationMember `gorm:"foreignKey:OrganizationID" json:"members,omitempty"`
}

type OrganizationMember struct {
	ID             string    `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"`
	OrganizationID string    `gorm:"not null" json:"organization_id"`
	UserID         string    `gorm:"not null" json:"user_id"`
	Role           UserRole  `gorm:"default:'MEMBER'" json:"role"`
	JoinedAt       time.Time `gorm:"autoCreateTime" json:"joined_at"`
}

type AuditLog struct {
	ID             string    `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"`
	UserID         string    `gorm:"not null" json:"user_id"`
	OrganizationID string    `json:"organization_id"`
	Action         string    `gorm:"not null" json:"action"`          // e.g., "SEARCH", "VIEW_DEKA"
	TargetResource string    `json:"target_resource"`                 // e.g., "Deka:2566/1234"
	Details        string    `gorm:"type:text" json:"details"`        // JSON string
	IPAddress      string    `json:"ip_address"`
	Timestamp      time.Time `gorm:"autoCreateTime" json:"timestamp"`
}

type Conversation struct {
	ID        string    `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"`
	UserID    string    `gorm:"not null" json:"user_id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`

	// Relationships
	Messages []Message `gorm:"foreignKey:ConversationID;constraint:OnDelete:CASCADE" json:"messages,omitempty"`
}

type Message struct {
	ID             string    `gorm:"primaryKey;type:text;default:(uuid_generate_v4())" json:"id"`
	ConversationID string    `gorm:"not null" json:"conversation_id"`
	Role           string    `gorm:"not null" json:"role"` // 'user' or 'model'
	Content        string    `gorm:"type:text;not null" json:"content"`
	CreatedAt      time.Time `gorm:"autoCreateTime" json:"created_at"`
}
