package com.flare.guardbox

import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.flare.guardbox.adapters.ActivityLogAdapter
import com.flare.guardbox.model.ActivityLog
import com.flare.guardbox.model.GuardBoxStatus
import com.flare.guardbox.model.User
import com.flare.guardbox.utils.FirebaseHelper
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.card.MaterialCardView
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.database.*

class MainActivity : AppCompatActivity() {

    private lateinit var tvLockStatus: TextView
    private lateinit var tvPackageStatus: TextView
    private lateinit var btnLock: Button
    private lateinit var btnUnlock: Button
    private lateinit var rvNotifications: RecyclerView
    private lateinit var bottomNavigation: BottomNavigationView
    private lateinit var cardViewAddDevice: MaterialCardView
    private lateinit var cardViewRefresh: MaterialCardView
    private lateinit var versionText: TextView

    // Optional views
    private var tvBatteryStatus: TextView? = null
    private var tvConnectionStatus: TextView? = null
    private var tvLastUpdate: TextView? = null

    private val firebaseHelper = FirebaseHelper.getInstance()
    private var currentDeviceId: String? = null
    private var currentDeviceStatus: String = "offline"
    private var currentDeviceRef: DatabaseReference? = null
    private var userDevicesRef: DatabaseReference? = null

    private val activityLogs = mutableListOf<ActivityLog>()
    private lateinit var activityLogAdapter: ActivityLogAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // User login check
        if (firebaseHelper.getCurrentUser() == null) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            return
        }

        initializeViews()
        setupRecyclerView()
        setupButtonListeners()
        setupBottomNavigation()
        setupFirebaseReferences()
        getUserDeviceId()
        showDemoData()
        setupNetworkMonitoring()
    }

    private fun initializeViews() {
        // Main views
        tvLockStatus = findViewById(R.id.tvLockStatus)
        tvPackageStatus = findViewById(R.id.tvPackageStatus)
        btnLock = findViewById(R.id.btnLock)
        btnUnlock = findViewById(R.id.btnUnlock)
        rvNotifications = findViewById(R.id.rvNotifications)
        bottomNavigation = findViewById(R.id.bottomNavigation)
        versionText = findViewById(R.id.versionText)

        // Card views
        cardViewAddDevice = findViewById(R.id.cardViewAddDevice)
        cardViewRefresh = findViewById(R.id.cardViewRefresh)

        // Optional status views
        try {
            tvBatteryStatus = findViewById(R.id.tvBatteryStatus)
            tvConnectionStatus = findViewById(R.id.tvConnectionStatus)
            tvLastUpdate = findViewById(R.id.tvLastUpdate)
        } catch (e: Exception) {
            // Continue silently if optional views are missing
        }
    }

    private fun setupRecyclerView() {
        activityLogAdapter = ActivityLogAdapter(activityLogs)
        rvNotifications.layoutManager = LinearLayoutManager(this)
        rvNotifications.adapter = activityLogAdapter
    }

    private fun setupButtonListeners() {
        // Main buttons
        btnLock.setOnClickListener { sendLockCommand(true) }
        btnUnlock.setOnClickListener { sendLockCommand(false) }

        // Quick access cards
        cardViewAddDevice.setOnClickListener { showAddDeviceDialog() }
        cardViewRefresh.setOnClickListener {
            refreshDeviceStatus()
            Toast.makeText(this, "Refreshing...", Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupBottomNavigation() {
        bottomNavigation.setOnNavigationItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> true // Already on home page
                R.id.nav_history -> {
                    startActivity(Intent(this, HistoryActivity::class.java))
                    true
                }
                R.id.nav_settings -> {
                    startActivity(Intent(this, SettingsActivity::class.java))
                    true
                }
                else -> false
            }
        }
    }

    private fun setupFirebaseReferences() {
        val userId = FirebaseAuth.getInstance().currentUser?.uid
        if (userId != null) {
            userDevicesRef = FirebaseDatabase.getInstance().getReference("users/$userId/devices")
        } else {
            Toast.makeText(this, "Please log in to access your devices", Toast.LENGTH_LONG).show()
        }
    }

    private fun getUserDeviceId() {
        val userId = firebaseHelper.getCurrentUser()?.uid
        if (userId != null) {
            firebaseHelper.getUserProfile(userId, object : ValueEventListener {
                override fun onDataChange(dataSnapshot: DataSnapshot) {
                    val user = dataSnapshot.getValue(User::class.java)
                    if (user != null && user.deviceIds.isNotEmpty()) {
                        currentDeviceId = user.deviceIds[0] // Get first device
                        currentDeviceRef = FirebaseDatabase.getInstance()
                            .getReference("devices").child(currentDeviceId!!)
                        loadBoxStatus()
                        loadActivityLogs()
                    } else {
                        // No device - will show demo data
                        showNoDeviceMessage()
                    }
                }

                override fun onCancelled(databaseError: DatabaseError) {
                    Toast.makeText(
                        this@MainActivity,
                        "Failed to load user info: ${databaseError.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            })
        }
    }

    private fun loadBoxStatus() {
        // Reset UI to offline state
        setOfflineState()
        currentDeviceId?.let { deviceId ->
            firebaseHelper.getBoxStatus(deviceId, object : ValueEventListener {
                override fun onDataChange(dataSnapshot: DataSnapshot) {
                    val status = dataSnapshot.getValue(GuardBoxStatus::class.java)
                    if (status != null) {
                        // Device data retrieved, switch to online state
                        currentDeviceStatus = "online"
                        setOnlineState(status)
                    } else {
                        setOfflineState()
                    }
                }

                override fun onCancelled(databaseError: DatabaseError) {
                    setOfflineState()
                    Toast.makeText(
                        this@MainActivity,
                        "Failed to load box status: ${databaseError.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            })
        } ?: run {
            // No device ID
            setOfflineState()
        }
    }

    private fun setOfflineState() {
        currentDeviceStatus = "offline"
        // System status
        tvBatteryStatus?.text = "Unavailable"
        tvBatteryStatus?.setTextColor(resources.getColor(R.color.colorGrey))
        tvConnectionStatus?.text = "Offline"
        tvConnectionStatus?.setTextColor(resources.getColor(R.color.colorDanger))
        tvLastUpdate?.text = "Never"
        // Disable buttons
        btnLock.isEnabled = false
        btnUnlock.isEnabled = false
        // Lock status
        tvLockStatus.text = "UNKNOWN"
        tvLockStatus.setTextColor(resources.getColor(R.color.colorGrey))
        // Package status
        tvPackageStatus.text = "UNKNOWN"
        tvPackageStatus.setTextColor(resources.getColor(R.color.colorGrey))
    }

    private fun setOnlineState(status: GuardBoxStatus) {
        // Battery status
        if (status.batteryLevel != null) {
            tvBatteryStatus?.text = "${status.batteryLevel}%"
            val batteryColor = when {
                status.batteryLevel > 50 -> R.color.colorSuccess
                status.batteryLevel > 20 -> R.color.colorWarning
                else -> R.color.colorDanger
            }
            tvBatteryStatus?.setTextColor(resources.getColor(batteryColor))
        } else {
            tvBatteryStatus?.text = "Unknown"
            tvBatteryStatus?.setTextColor(resources.getColor(R.color.colorGrey))
        }

        // Connection status
        tvConnectionStatus?.text = "Connected"
        tvConnectionStatus?.setTextColor(resources.getColor(R.color.colorSuccess))
        // Last update
        tvLastUpdate?.text = "Now"
        // Update UI buttons
        updateUI(status)
    }

    private fun loadActivityLogs() {
        currentDeviceId?.let { deviceId ->
            firebaseHelper.getActivityLogs(deviceId, object : ValueEventListener {
                override fun onDataChange(dataSnapshot: DataSnapshot) {
                    activityLogs.clear()
                    for (snapshot in dataSnapshot.children) {
                        val log = snapshot.getValue(ActivityLog::class.java)
                        if (log != null) {
                            activityLogs.add(log)
                        }
                    }
                    if (activityLogs.isEmpty()) {
                        // No activity - add demo
                        addDemoActivities(deviceId)
                    } else {
                        // Sort newest first
                        activityLogs.sortByDescending { it.timestamp }
                        activityLogAdapter.notifyDataSetChanged()
                    }
                }

                override fun onCancelled(databaseError: DatabaseError) {
                    Toast.makeText(
                        this@MainActivity,
                        "Failed to load activity logs: ${databaseError.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            })
        }
    }

    private fun updateUI(status: GuardBoxStatus) {
        updateLockUI(status.isLocked)
        updatePackageUI(status.hasPackage)
    }

    private fun updateLockUI(isLocked: Boolean) {
        if (isLocked) {
            tvLockStatus.text = "LOCKED"
            tvLockStatus.setTextColor(resources.getColor(R.color.colorSuccess))
            btnLock.isEnabled = false
            btnUnlock.isEnabled = true
        } else {
            tvLockStatus.text = "UNLOCKED"
            tvLockStatus.setTextColor(resources.getColor(R.color.colorDanger))
            btnLock.isEnabled = true
            btnUnlock.isEnabled = false
        }
    }

    private fun updatePackageUI(hasPackage: Boolean) {
        if (hasPackage) {
            tvPackageStatus.text = "PACKAGE INSIDE"
            tvPackageStatus.setTextColor(resources.getColor(R.color.colorAccent))
        } else {
            tvPackageStatus.text = "EMPTY"
            tvPackageStatus.setTextColor(resources.getColor(R.color.colorGrey))
        }
    }

    private fun showDemoData() {
        // System status demo values
        tvBatteryStatus?.text = "85%"
        tvConnectionStatus?.text = "Connected"
        tvLastUpdate?.text = "Now"
    }

    private fun showNoDeviceMessage() {
        Toast.makeText(
            this,
            "No GuardBox device added yet. Use 'Add Device' button to add one.",
            Toast.LENGTH_LONG
        ).show()
        btnLock.isEnabled = false
        btnUnlock.isEnabled = false
    }

    private fun showAddDeviceDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_add_device, null)
        val deviceIdInput = dialogView.findViewById<EditText>(R.id.etDeviceId)
        val deviceNameInput = dialogView.findViewById<EditText>(R.id.etDeviceName)

        val dialog = AlertDialog.Builder(this)
            .setTitle("Add New GuardBox")
            .setView(dialogView)
            .setPositiveButton("Add", null) // Set to null and override below
            .setNegativeButton("Cancel", null)
            .create()

        dialog.show()

        // Override positive button to check for empty input
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            val deviceId = deviceIdInput.text.toString().trim()
            if (deviceId.isEmpty()) {
                deviceIdInput.error = "Device ID is required"
                return@setOnClickListener
            }
            // Add device and close dialog
            addNewDevice(deviceId)
            dialog.dismiss()
        }
    }

    private fun refreshDeviceStatus() {
        loadBoxStatus()
        loadActivityLogs()
        // Update system status
        tvBatteryStatus?.text = "85%"
        tvConnectionStatus?.text = "Connected"
        tvLastUpdate?.text = "Now"
    }

    private fun addDemoActivities(deviceId: String) {
        val now = System.currentTimeMillis()
        val oneHour = 60 * 60 * 1000L
        activityLogs.add(ActivityLog("SYSTEM_STATUS", now, "GuardBox came online", deviceId))
        activityLogs.add(ActivityLog("BOX_LOCKED", now - oneHour, "Box locked automatically", deviceId))
        activityLogs.add(ActivityLog("SYSTEM_STATUS", now - (2 * oneHour), "Device initialized", deviceId))
        activityLogAdapter.notifyDataSetChanged()
    }

    private fun addNewDevice(deviceId: String) {
        // 1. Get user ID
        val userId = FirebaseAuth.getInstance().currentUser?.uid ?: return
        // 2. Show loading dialog
        val loadingDialog = AlertDialog.Builder(this)
            .setMessage("Adding device...")
            .setCancelable(false)
            .create()
        loadingDialog.show()

        // 3. Add device to database
        val newDeviceRef = FirebaseDatabase.getInstance().getReference("devices").child(deviceId)
        val deviceData = HashMap<String, Any>()
        deviceData["name"] = "GuardBox $deviceId"
        deviceData["status"] = "online" // Initially online
        deviceData["lock"] = true
        deviceData["package"] = false
        deviceData["connectionStatus"] = "online"

        newDeviceRef.setValue(deviceData)
            .addOnSuccessListener {
                // 4. Save user-device relationship
                FirebaseDatabase.getInstance()
                    .getReference("users/$userId/devices/$deviceId")
                    .setValue(true)
                    .addOnSuccessListener {
                        loadingDialog.dismiss()
                        Toast.makeText(this, "Device added successfully", Toast.LENGTH_SHORT).show()
                        // 5. Set current device
                        currentDeviceId = deviceId
                        currentDeviceRef = newDeviceRef
                        currentDeviceStatus = "online"
                        // 6. Update screen
                        refreshDeviceStatus()
                    }
                    .addOnFailureListener { e ->
                        loadingDialog.dismiss()
                        Toast.makeText(this, "Failed to link device: ${e.message}", Toast.LENGTH_LONG).show()
                    }
            }
            .addOnFailureListener { e ->
                loadingDialog.dismiss()
                Toast.makeText(this, "Failed to add device: ${e.message}", Toast.LENGTH_LONG).show()
            }
    }

    private fun loadDevices() {
        // Load all registered devices
        FirebaseDatabase.getInstance().getReference("devices")
            .addListenerForSingleValueEvent(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    // Update UI with devices list
                    refreshDeviceStatus()
                }

                override fun onCancelled(error: DatabaseError) {
                    Toast.makeText(baseContext, "Failed to load devices: ${error.message}", Toast.LENGTH_SHORT).show()
                }
            })
    }

    private fun sendLockCommand(lock: Boolean) {
        if (currentDeviceId == null) {
            showNoDeviceMessage()
            return
        }
        if (currentDeviceStatus != "online") {
            // Not blocking execution, but giving feedback
            Toast.makeText(this, "Device is offline. Command may not be received immediately.", Toast.LENGTH_LONG).show()
        }

        currentDeviceId?.let { deviceId ->
            // Send lock command
            firebaseHelper.setBoxLockStatus(deviceId, lock)
            // Update UI immediately (without waiting for Firebase response)
            updateLockUI(lock)
            // Save active device for later use
            val editor = getSharedPreferences("GuardBox", MODE_PRIVATE).edit()
            editor.putString("lastDeviceId", deviceId)
            editor.apply()

            val message = if (lock) "Lock command sent" else "Unlock command sent"
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show()

            // Add activity log
            addActivityLog(
                deviceId,
                if (lock) "BOX_LOCKED" else "BOX_UNLOCKED",
                if (lock) "Box locked" else "Box unlocked"
            )
        }
    }

    private fun addActivityLog(deviceId: String, type: String, message: String) {
        val key = FirebaseDatabase.getInstance()
            .getReference("devices/$deviceId/activities").push().key ?: return
        val timestamp = System.currentTimeMillis()
        val activity = ActivityLog(type, timestamp, message, deviceId)
        FirebaseDatabase.getInstance()
            .getReference("devices/$deviceId/activities/$key")
            .setValue(activity)
    }

    private fun setupNetworkMonitoring() {
        FirebaseDatabase.getInstance().getReference(".info/connected")
            .addValueEventListener(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    val connected = snapshot.getValue(Boolean::class.java) ?: false
                    if (!connected) {
                        Toast.makeText(baseContext, "Network connection lost", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onCancelled(error: DatabaseError) {
                    // Handle error
                }
            })
    }
}
