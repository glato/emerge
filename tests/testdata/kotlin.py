# Borrowed for testing with real test data from https://github.com/Tapadoo/Alerter

KOTLIN_TEST_FILES = {"Alert.kt": """

package com.tapadoo.alerter

import android.annotation.SuppressLint
import android.annotation.TargetApi
import android.content.Context
import android.graphics.*
import android.graphics.drawable.Drawable
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.text.TextUtils
import android.util.AttributeSet
import android.util.Log
import android.view.*
import android.view.animation.Animation
import android.view.animation.AnimationUtils
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import androidx.annotation.*
import androidx.appcompat.content.res.AppCompatResources
import androidx.appcompat.view.ContextThemeWrapper
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.widget.TextViewCompat
import com.tapadoo.alerter.utils.getDimenPixelSize
import com.tapadoo.alerter.utils.getRippleDrawable
import com.tapadoo.alerter.utils.notchHeight
import kotlinx.android.synthetic.main.alerter_alert_default_layout.view.*
import kotlinx.android.synthetic.main.alerter_alert_view.view.*

/**
 * Custom Alert View
 *
 * @author Kevin Murphy, Tapadoo, Dublin, Ireland, Europe, Earth.
 * @since 26/01/2016
 */
@SuppressLint("ViewConstructor")
class Alert @JvmOverloads constructor(context: Context,
                                      @LayoutRes layoutId: Int,
                                      attrs: AttributeSet? = null,
                                      defStyle: Int = 0)
    : FrameLayout(context, attrs, defStyle), View.OnClickListener, Animation.AnimationListener, SwipeDismissTouchListener.DismissCallbacks {

    private var onShowListener: OnShowAlertListener? = null
    internal var onHideListener: OnHideAlertListener? = null

    internal var enterAnimation: Animation = AnimationUtils.loadAnimation(context, R.anim.alerter_slide_in_from_top)
    internal var exitAnimation: Animation = AnimationUtils.loadAnimation(context, R.anim.alerter_slide_out_to_top)

    internal var duration = DISPLAY_TIME_IN_SECONDS

    private var showIcon: Boolean = true
    private var enableIconPulse = true
    private var enableInfiniteDuration: Boolean = false
    private var enableProgress: Boolean = false

    private var showRightIcon: Boolean = false
    private var enableClickAnimation: Boolean = true
    private var enableRightIconPurse = true

    private var runningAnimation: Runnable? = null

    private var isDismissible = true

    private var buttons = ArrayList<Button>()
    var buttonTypeFace: Typeface? = null

    /**
     * Flag to ensure we only set the margins once
     */
    private var marginSet: Boolean = false

    /**
     * Flag to enable / disable haptic feedback
     */
    private var vibrationEnabled = true

    /**
     * Uri to set sound
     */
    private var soundUri: Uri? = null

    /**
     * Sets the Layout Gravity of the Alert
     *
     * @param layoutGravity Layout Gravity of the Alert
     */
    var layoutGravity = Gravity.TOP
        set(value) {

            if (value != Gravity.TOP) {
                enterAnimation = AnimationUtils.loadAnimation(context, R.anim.alerter_slide_in_from_bottom)
                exitAnimation = AnimationUtils.loadAnimation(context, R.anim.alerter_slide_out_to_bottom)
            }

            field = value
        }

    /**
     * Sets the Gravity of the Alert
     *
     * @param contentGravity Gravity of the Alert
     */
    var contentGravity: Int
        get() = (llAlertBackground?.layoutParams as LayoutParams).gravity
        set(contentGravity) {

            (tvTitle?.layoutParams as? LinearLayout.LayoutParams)?.apply {
                gravity = contentGravity
            }

            val paramsText = tvText?.layoutParams as? LinearLayout.LayoutParams
            paramsText?.gravity = contentGravity
            tvText?.layoutParams = paramsText
        }

    val layoutContainer: View? by lazy { findViewById<View>(R.id.vAlertContentContainer) }

    private val navigationBarHeight by lazy {
        val dimenId = resources.getIdentifier("navigation_bar_height", "dimen", "android")
        resources.getDimensionPixelSize(dimenId)
    }

    init {
        inflate(context, R.layout.alerter_alert_view, this)

        vAlertContentContainer.layoutResource = layoutId
        vAlertContentContainer.inflate()

        isHapticFeedbackEnabled = true

        ViewCompat.setTranslationZ(this, Integer.MAX_VALUE.toFloat())

        llAlertBackground.setOnClickListener(this)
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()

        llAlertBackground.apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                foreground = if (enableClickAnimation.not()) {
                    null
                } else {
                    context.getRippleDrawable()
                }
            }

            (layoutParams as LayoutParams).gravity = layoutGravity

            if (layoutGravity != Gravity.TOP) {
                setPadding(
                        paddingLeft, getDimenPixelSize(R.dimen.alerter_padding_default),
                        paddingRight, getDimenPixelSize(R.dimen.alerter_alert_padding)
                )
            }
        }

        (layoutParams as MarginLayoutParams).apply {
            if (layoutGravity != Gravity.TOP) {
                bottomMargin = navigationBarHeight
            }
        }

        enterAnimation.setAnimationListener(this)

        // Set Animation to be Run when View is added to Window
        animation = enterAnimation

        // Add all buttons
        buttons.forEach { button ->
            buttonTypeFace?.let { button.typeface = it }
            llButtonContainer.addView(button)
        }
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        if (!marginSet) {
            marginSet = true

            // Add a negative top margin to compensate for overshoot enter animation
            (layoutParams as MarginLayoutParams).topMargin = getDimenPixelSize(R.dimen.alerter_alert_negative_margin_top)

            // Check for Cutout
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                llAlertBackground.apply {
                    setPadding(paddingLeft, paddingTop + (notchHeight() / 2), paddingRight, paddingBottom)
                }
            }
        }

        super.onMeasure(widthMeasureSpec, heightMeasureSpec)
    }

    // Release resources once view is detached.
    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()

        enterAnimation.setAnimationListener(null)
    }

    /* Override Methods */

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent): Boolean {
        super.performClick()
        return super.onTouchEvent(event)
    }

    override fun onClick(v: View) {
        if (isDismissible) {
            hide()
        }
    }

    override fun setOnClickListener(listener: OnClickListener?) {
        llAlertBackground.setOnClickListener(listener)
    }

    override fun setVisibility(visibility: Int) {
        super.setVisibility(visibility)
        for (i in 0 until childCount) {
            getChildAt(i).visibility = visibility
        }
    }

    /* Interface Method Implementations */

    override fun onAnimationStart(animation: Animation) {
        if (!isInEditMode) {
            visibility = View.VISIBLE

            if (vibrationEnabled) {
                performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
            }
            soundUri?.let {
                val r = RingtoneManager.getRingtone(context, soundUri)
                r.play()
            }

            if (enableProgress) {
                ivIcon?.visibility = View.INVISIBLE
                ivRightIcon?.visibility = View.INVISIBLE
                pbProgress?.visibility = View.VISIBLE
            } else {
                if (showIcon) {
                    ivIcon?.visibility = View.VISIBLE
                    // Only pulse if we're not showing the progress
                    if (enableIconPulse) {
                        ivIcon?.startAnimation(AnimationUtils.loadAnimation(context, R.anim.alerter_pulse))
                    }
                } else {
                    flIconContainer?.visibility = View.GONE
                }
                if (showRightIcon) {
                    ivRightIcon?.visibility = View.VISIBLE

                    if (enableRightIconPurse) {
                        ivRightIcon?.startAnimation(AnimationUtils.loadAnimation(context, R.anim.alerter_pulse))
                    }
                } else {
                    flRightIconContainer?.visibility = View.GONE
                }
            }
        }
    }

    override fun onAnimationEnd(animation: Animation) {
        onShowListener?.onShow()

        startHideAnimation()
    }

    @TargetApi(Build.VERSION_CODES.HONEYCOMB)
    private fun startHideAnimation() {
        //Start the Handler to clean up the Alert
        if (!enableInfiniteDuration) {
            runningAnimation = Runnable { hide() }

            postDelayed(runningAnimation, duration)
        }
    }

    override fun onAnimationRepeat(animation: Animation) {
        //Ignore
    }

    /* Clean Up Methods */

    /**
     * Cleans up the currently showing alert view.
     */
    private fun hide() {
        try {
            exitAnimation.setAnimationListener(object : Animation.AnimationListener {
                override fun onAnimationStart(animation: Animation) {
                    llAlertBackground?.setOnClickListener(null)
                    llAlertBackground?.isClickable = false
                }

                override fun onAnimationEnd(animation: Animation) {
                    removeFromParent()
                }

                override fun onAnimationRepeat(animation: Animation) {
                    //Ignore
                }
            })

            startAnimation(exitAnimation)
        } catch (ex: Exception) {
            Log.e(javaClass.simpleName, Log.getStackTraceString(ex))
        }
    }

    /**
     * Removes Alert View from its Parent Layout
     */
    internal fun removeFromParent() {
        clearAnimation()
        visibility = View.GONE

        postDelayed(object : Runnable {
            override fun run() {
                try {
                    if (parent != null) {
                        try {
                            (parent as ViewGroup).removeView(this@Alert)

                            onHideListener?.onHide()
                        } catch (ex: Exception) {
                            Log.e(javaClass.simpleName, "Cannot remove from parent layout")
                        }
                    }
                } catch (ex: Exception) {
                    Log.e(javaClass.simpleName, Log.getStackTraceString(ex))
                }
            }
        }, CLEAN_UP_DELAY_MILLIS.toLong())
    }

    /* Setters and Getters */

    /**
     * Sets the Alert Background colour
     *
     * @param color The qualified colour integer
     */
    fun setAlertBackgroundColor(@ColorInt color: Int) {
        llAlertBackground.setBackgroundColor(color)
    }

    /**
     * Sets the Alert Background Drawable Resource
     *
     * @param resource The qualified drawable integer
     */
    fun setAlertBackgroundResource(@DrawableRes resource: Int) {
        llAlertBackground.setBackgroundResource(resource)
    }

    /**
     * Sets the Alert Background Drawable
     *
     * @param drawable The qualified drawable
     */
    fun setAlertBackgroundDrawable(drawable: Drawable) {
        ViewCompat.setBackground(llAlertBackground, drawable)
    }

    /**
     * Sets the Title of the Alert
     *
     * @param titleId String resource id of the Alert title
     */
    fun setTitle(@StringRes titleId: Int) {
        setTitle(context.getString(titleId))
    }

    /**
     * Sets the Text of the Alert
     *
     * @param textId String resource id of the Alert text
     */
    fun setText(@StringRes textId: Int) {
        setText(context.getString(textId))
    }

    /**
     * Disable touches while the Alert is showing
     */
    fun disableOutsideTouch() {
        flClickShield.isClickable = true
    }

    /**
     * Sets the Title of the Alert
     *
     * @param title CharSequence object to be used as the Alert title
     */
    fun setTitle(title: CharSequence) {
        if (!TextUtils.isEmpty(title)) {
            tvTitle?.visibility = View.VISIBLE
            tvTitle?.text = title
        }
    }

    /**
     * Set the Title's text appearance of the Title
     *
     * @param textAppearance The style resource id
     */
    fun setTitleAppearance(@StyleRes textAppearance: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            tvTitle?.setTextAppearance(textAppearance)
        } else {
            TextViewCompat.setTextAppearance(tvTitle, textAppearance)
        }
    }

    /**
     * Set the Title's typeface
     *
     * @param typeface The typeface to use
     */
    fun setTitleTypeface(typeface: Typeface) {
        tvTitle?.typeface = typeface
    }

    /**
     * Set the Text's typeface
     *
     * @param typeface The typeface to use
     */
    fun setTextTypeface(typeface: Typeface) {
        tvText?.typeface = typeface
    }

    /**
     * Sets the Text of the Alert
     *
     * @param text CharSequence object to be used as the Alert text
     */
    fun setText(text: CharSequence) {
        if (!TextUtils.isEmpty(text)) {
            tvText?.visibility = View.VISIBLE
            tvText?.text = text
        }
    }

    /**
     * Set the Text's text appearance of the Title
     *
     * @param textAppearance The style resource id
     */
    fun setTextAppearance(@StyleRes textAppearance: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            tvText?.setTextAppearance(textAppearance)
        } else {
            TextViewCompat.setTextAppearance(tvText, textAppearance)
        }
    }

    /**
     * Set the inline icon for the Alert
     *
     * @param iconId Drawable resource id of the icon to use in the Alert
     */
    fun setIcon(@DrawableRes iconId: Int) {
        ivIcon?.setImageDrawable(AppCompatResources.getDrawable(context, iconId))
    }

    /**
     * Set the icon color for the Alert
     *
     * @param color Color int
     */
    fun setIconColorFilter(@ColorInt color: Int) {
        ivIcon?.setColorFilter(color)
    }

    /**
     * Set the icon color for the Alert
     *
     * @param colorFilter ColorFilter
     */
    fun setIconColorFilter(colorFilter: ColorFilter) {
        ivIcon?.colorFilter = colorFilter
    }

    /**
     * Set the icon color for the Alert
     *
     * @param color Color int
     * @param mode  PorterDuff.Mode
     */
    fun setIconColorFilter(@ColorInt color: Int, mode: PorterDuff.Mode) {
        ivIcon?.setColorFilter(color, mode)
    }

    /**
     * Set the inline icon for the Alert
     *
     * @param bitmap Bitmap image of the icon to use in the Alert.
     */
    fun setIcon(bitmap: Bitmap) {
        ivIcon?.setImageBitmap(bitmap)
    }

    /**
     * Set the inline icon for the Alert
     *
     * @param drawable Drawable image of the icon to use in the Alert.
     */
    fun setIcon(drawable: Drawable) {
        ivIcon?.setImageDrawable(drawable)
    }

    /**
     * Set the inline icon size for the Alert
     *
     * @param size Dimension int.
     */
    fun setIconSize(@DimenRes size: Int) {
        val pixelSize = getDimenPixelSize(size)
        setIconPixelSize(pixelSize)
    }

    /**
     * Set the inline icon size for the Alert
     *
     * @param size Icon size in pixel.
     */
    fun setIconPixelSize(@Px size: Int) {
        ivIcon.layoutParams = ivIcon.layoutParams.apply {
            width = size
            height = size
            minimumWidth = size
            minimumHeight = size
        }
    }

    /**
     * Set whether to show the icon in the alert or not
     *
     * @param showIcon True to show the icon, false otherwise
     */
    fun showIcon(showIcon: Boolean) {
        this.showIcon = showIcon
    }

    /**
     * Set the inline right icon for the Alert
     *
     * @param iconId Drawable resource id of the right icon to use in the Alert
     */
    fun setRightIcon(@DrawableRes iconId: Int) {
        ivRightIcon?.setImageDrawable(AppCompatResources.getDrawable(context, iconId))
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param color Color int
     */
    fun setRightIconColorFilter(@ColorInt color: Int) {
        ivRightIcon?.setColorFilter(color)
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param colorFilter ColorFilter
     */
    fun setRightIconColorFilter(colorFilter: ColorFilter) {
        ivRightIcon?.colorFilter = colorFilter
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param color Color int
     * @param mode  PorterDuff.Mode
     */
    fun setRightIconColorFilter(@ColorInt color: Int, mode: PorterDuff.Mode) {
        ivRightIcon?.setColorFilter(color, mode)
    }

    /**
     * Set the inline right icon for the Alert
     *
     * @param bitmap Bitmap image of the right icon to use in the Alert.
     */
    fun setRightIcon(bitmap: Bitmap) {
        ivRightIcon?.setImageBitmap(bitmap)
    }

    /**
     * Set the inline right icon for the Alert
     *
     * @param drawable Drawable image of the right icon to use in the Alert.
     */
    fun setRightIcon(drawable: Drawable) {
        ivRightIcon?.setImageDrawable(drawable)
    }

    /**
     * Set the inline right icon size for the Alert
     *
     * @param size Dimension int.
     */
    fun setRightIconSize(@DimenRes size: Int) {
        val pixelSize = context.resources.getDimensionPixelSize(size)
        setRightIconPixelSize(pixelSize)
    }

    /**
     * Set the inline right icon size for the Alert
     *
     * @param size Icon size in pixel.
     */
    fun setRightIconPixelSize(@Px size: Int) {
        ivRightIcon.layoutParams = ivRightIcon.layoutParams.apply {
            width = size
            height = size
            minimumWidth = size
            minimumHeight = size
        }
    }

    /**
     * Set whether to show the right icon in the alert or not
     *
     * @param showRightIcon True to show the right icon, false otherwise
     */
    fun showRightIcon(showRightIcon: Boolean) {
        this.showRightIcon = showRightIcon
    }

    /**
     * Set whether to show the animation on focus/pressed states
     *
     * @param enabled True to show the animation, false otherwise
     */
    fun enableClickAnimation(enabled: Boolean) {
        this.enableClickAnimation = enabled
    }

    /**
     * Set right icon position
     *
     * @param position gravity of an right icon's parent. Can be: Gravity.TOP,
     * Gravity.CENTER, Gravity.CENTER_VERTICAL or Gravity.BOTTOM
     */
    fun setRightIconPosition(position: Int) {
        if (position == Gravity.TOP
                || position == Gravity.CENTER
                || position == Gravity.CENTER_VERTICAL
                || position == Gravity.BOTTOM) {
            flRightIconContainer.layoutParams = (flRightIconContainer.layoutParams as LinearLayout.LayoutParams).apply {
                gravity = position
            }
        }
    }

    /**
     * Set if the alerter is isDismissible or not
     *
     * @param dismissible True if alert can be dismissed
     */
    fun setDismissible(dismissible: Boolean) {
        this.isDismissible = dismissible
    }

    /**
     * Get if the alert is isDismissible
     * @return
     */
    fun isDismissible(): Boolean {
        return isDismissible
    }

    /**
     * Set whether to enable swipe to dismiss or not
     */
    fun enableSwipeToDismiss() {
        llAlertBackground.let {
            it.setOnTouchListener(SwipeDismissTouchListener(it, object : SwipeDismissTouchListener.DismissCallbacks {
                override fun canDismiss(): Boolean {
                    return true
                }

                override fun onDismiss(view: View) {
                    removeFromParent()
                }

                override fun onTouch(view: View, touch: Boolean) {
                    // Ignore
                }
            }))
        }
    }

    /**
     * Set if the Icon should pulse or not
     *
     * @param shouldPulse True if the icon should be animated
     */
    fun pulseIcon(shouldPulse: Boolean) {
        this.enableIconPulse = shouldPulse
    }

    /**
     * Set if the Right Icon should pulse or not
     *
     * @param shouldPulse True if the right icon should be animated
     */
    fun pulseRightIcon(shouldPulse: Boolean) {
        this.enableRightIconPurse = shouldPulse
    }

    /**
     * Set if the duration of the alert is infinite
     *
     * @param enableInfiniteDuration True if the duration of the alert is infinite
     */
    fun setEnableInfiniteDuration(enableInfiniteDuration: Boolean) {
        this.enableInfiniteDuration = enableInfiniteDuration
    }

    /**
     * Enable or disable progress bar
     *
     * @param enableProgress True to enable, False to disable
     */
    fun setEnableProgress(enableProgress: Boolean) {
        this.enableProgress = enableProgress
    }

    /**
     * Set the Progress bar color from a color resource
     *
     * @param color The color resource
     */
    fun setProgressColorRes(@ColorRes color: Int) {
        pbProgress?.progressDrawable?.colorFilter = LightingColorFilter(MUL, ContextCompat.getColor(context, color))
    }

    /**
     * Set the Progress bar color from a color resource
     *
     * @param color The color resource
     */
    fun setProgressColorInt(@ColorInt color: Int) {
        pbProgress?.progressDrawable?.colorFilter = LightingColorFilter(MUL, color)
    }

    /**
     * Set the alert's listener to be fired on the alert being fully shown
     *
     * @param listener Listener to be fired
     */
    fun setOnShowListener(listener: OnShowAlertListener) {
        this.onShowListener = listener
    }

    /**
     * Enable or Disable haptic feedback
     *
     * @param vibrationEnabled True to enable, false to disable
     */
    fun setVibrationEnabled(vibrationEnabled: Boolean) {
        this.vibrationEnabled = vibrationEnabled
    }

    /**
     * Set sound Uri
     *
     * @param soundUri To set sound Uri (raw folder)
     */
    fun setSound(soundUri: Uri?) {
        this.soundUri = soundUri
    }

    /**
     * Show a button with the given text, and on click listener
     *
     * @param text The text to display on the button
     * @param onClick The on click listener
     */
    fun addButton(text: CharSequence, @StyleRes style: Int, onClick: OnClickListener) {
        Button(ContextThemeWrapper(context, style), null, style).apply {
            this.text = text
            this.setOnClickListener(onClick)

            buttons.add(this)
        }

        // Alter padding
        llAlertBackground?.apply {
            this.setPadding(this.paddingLeft, this.paddingTop, this.paddingRight, this.paddingBottom / 2)
        }
    }

    /**
     * @return the TextView for the title
     */
    fun getTitle(): TextView {
        return tvTitle
    }

    /**
     * @return the TextView for the text
     */
    fun getText(): TextView {
        return tvText
    }

    override fun canDismiss(): Boolean {
        return isDismissible
    }

    override fun onDismiss(view: View) {
        flClickShield?.removeView(llAlertBackground)
    }

    override fun onTouch(view: View, touch: Boolean) {
        if (touch) {
            removeCallbacks(runningAnimation)
        } else {
            startHideAnimation()
        }
    }

    companion object {

        private const val CLEAN_UP_DELAY_MILLIS = 100

        /**
         * The amount of time the alert will be visible on screen in seconds
         */
        private const val DISPLAY_TIME_IN_SECONDS: Long = 3000
        private const val MUL = -0x1000000
    }
}
""", "Alerter.kt": """
package com.tapadoo.alerter

import android.app.Activity
import android.app.Dialog
import android.graphics.Bitmap
import android.graphics.ColorFilter
import android.graphics.PorterDuff
import android.graphics.Typeface
import android.graphics.drawable.Drawable
import android.media.RingtoneManager
import android.net.Uri
import android.os.Looper
import android.view.View
import android.view.ViewGroup
import android.view.animation.AnimationUtils
import androidx.annotation.*
import androidx.appcompat.app.AppCompatDialog
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import java.lang.ref.WeakReference

/**
 * Alert helper class. Will attach a temporary layout to the current activity's content, on top of
 * all other views. It should appear under the status bar.
 *
 * @author Kevin Murphy
 * @since 03/11/2015.
 */
class Alerter private constructor() {

    /**
     * Sets the Alert
     *
     * @param alert The Alert to be references and maintained
     */
    private var alert: Alert? = null

    /**
     * Shows the Alert, after it's built
     *
     * @return An Alert object check can be altered or hidden
     */
    fun show(): Alert? {
        //This will get the Activity Window's DecorView
        decorView?.get()?.let {
            android.os.Handler(Looper.getMainLooper()).post {
                it.addView(alert)
            }
        }

        return alert
    }

    /**
     * Sets the title of the Alert
     *
     * @param titleId Title String Resource
     * @return This Alerter
     */
    fun setTitle(@StringRes titleId: Int): Alerter {
        alert?.setTitle(titleId)

        return this
    }

    /**
     * Set Title of the Alert
     *
     * @param title Title as a CharSequence
     * @return This Alerter
     */
    fun setTitle(title: CharSequence): Alerter {
        alert?.setTitle(title)

        return this
    }

    /**
     * Set the Title's Typeface
     *
     * @param typeface Typeface to use
     * @return This Alerter
     */
    fun setTitleTypeface(typeface: Typeface): Alerter {
        alert?.setTitleTypeface(typeface)

        return this
    }

    /**
     * Set the Title's text appearance
     *
     * @param textAppearance The style resource id
     * @return This Alerter
     */
    fun setTitleAppearance(@StyleRes textAppearance: Int): Alerter {
        alert?.setTitleAppearance(textAppearance)

        return this
    }

    /**
     * Set Layout Gravity of the Alert
     *
     * @param layoutGravity of Alert
     * @return This Alerter
     */
    fun setLayoutGravity(layoutGravity: Int): Alerter {
        alert?.layoutGravity = layoutGravity

        return this
    }

    /**
     * Set Gravity of the Alert
     *
     * @param gravity Gravity of Alert
     * @return This Alerter
     */
    fun setContentGravity(gravity: Int): Alerter {
        alert?.contentGravity = gravity

        return this
    }

    /**
     * Sets the Alert Text
     *
     * @param textId Text String Resource
     * @return This Alerter
     */
    fun setText(@StringRes textId: Int): Alerter {
        alert?.setText(textId)

        return this
    }

    /**
     * Sets the Alert Text
     *
     * @param text CharSequence of Alert Text
     * @return This Alerter
     */
    fun setText(text: CharSequence): Alerter {
        alert?.setText(text)

        return this
    }

    /**
     * Set the Text's Typeface
     *
     * @param typeface Typeface to use
     * @return This Alerter
     */
    fun setTextTypeface(typeface: Typeface): Alerter {
        alert?.setTextTypeface(typeface)

        return this
    }

    /**
     * Set the Text's text appearance
     *
     * @param textAppearance The style resource id
     * @return This Alerter
     */
    fun setTextAppearance(@StyleRes textAppearance: Int): Alerter {
        alert?.setTextAppearance(textAppearance)

        return this
    }

    /**
     * Set the Alert's Background Colour
     *
     * @param colorInt Colour int value
     * @return This Alerter
     */
    fun setBackgroundColorInt(@ColorInt colorInt: Int): Alerter {
        alert?.setAlertBackgroundColor(colorInt)

        return this
    }

    /**
     * Set the Alert's Background Colour
     *
     * @param colorResId Colour Resource Id
     * @return This Alerter
     */
    fun setBackgroundColorRes(@ColorRes colorResId: Int): Alerter {
        decorView?.get()?.let {
            alert?.setAlertBackgroundColor(ContextCompat.getColor(it.context.applicationContext, colorResId))
        }

        return this
    }

    /**
     * Set the Alert's Background Drawable
     *
     * @param drawable Drawable
     * @return This Alerter
     */
    fun setBackgroundDrawable(drawable: Drawable): Alerter {
        alert?.setAlertBackgroundDrawable(drawable)

        return this
    }

    /**
     * Set the Alert's Background Drawable Resource
     *
     * @param drawableResId Drawable Resource Id
     * @return This Alerter
     */
    fun setBackgroundResource(@DrawableRes drawableResId: Int): Alerter {
        alert?.setAlertBackgroundResource(drawableResId)

        return this
    }

    /**
     * Set the Alert's Icon
     *
     * @param iconId The Drawable's Resource Idw
     * @return This Alerter
     */
    fun setIcon(@DrawableRes iconId: Int): Alerter {
        alert?.setIcon(iconId)

        return this
    }

    /**
     * Set the Alert's Icon
     *
     * @param bitmap The Bitmap object to use for the icon.
     * @return This Alerter
     */
    fun setIcon(bitmap: Bitmap): Alerter {
        alert?.setIcon(bitmap)

        return this
    }

    /**
     * Set the Alert's Icon
     *
     * @param drawable The Drawable to use for the icon.
     * @return This Alerter
     */
    fun setIcon(drawable: Drawable): Alerter {
        alert?.setIcon(drawable)

        return this
    }

    /**
     * Set the Alert's Icon size
     *
     * @param size Dimension int.
     * @return This Alerter
     */
    fun setIconSize(@DimenRes size: Int): Alerter {
        alert?.setIconSize(size)

        return this
    }

    /**
     * Set the Alert's Icon size
     *
     * @param size Icon size in pixel.
     * @return This Alerter
     */
    fun setIconPixelSize(@Px size: Int): Alerter {
        alert?.setIconPixelSize(size)

        return this
    }

    /**
     * Set the icon color for the Alert
     *
     * @param color Color int
     * @return This Alerter
     */
    fun setIconColorFilter(@ColorInt color: Int): Alerter {
        alert?.setIconColorFilter(color)

        return this
    }

    /**
     * Set the icon color for the Alert
     *
     * @param colorFilter ColorFilter
     * @return This Alerter
     */
    fun setIconColorFilter(colorFilter: ColorFilter): Alerter {
        alert?.setIconColorFilter(colorFilter)

        return this
    }

    /**
     * Set the icon color for the Alert
     *
     * @param color Color int
     * @param mode  PorterDuff.Mode
     * @return This Alerter
     */
    fun setIconColorFilter(@ColorInt color: Int, mode: PorterDuff.Mode): Alerter {
        alert?.setIconColorFilter(color, mode)

        return this
    }

    /**
     * Hide the Icon
     *
     * @return This Alerter
     */
    fun hideIcon(): Alerter {
        alert?.showIcon(false)

        return this
    }

    /**
     * Set the Alert's Right Icon
     *
     * @param iconId The Drawable's Resource Idw
     * @return This Alerter
     */
    fun setRightIcon(@DrawableRes rightIconId: Int): Alerter {
        alert?.setRightIcon(rightIconId)

        return this
    }

    /**
     * Set the Alert's Right Icon
     *
     * @param bitmap The Bitmap object to use for the right icon.
     * @return This Alerter
     */
    fun setRightIcon(bitmap: Bitmap): Alerter {
        alert?.setRightIcon(bitmap)

        return this
    }

    /**
     * Set the Alert's Right Icon
     *
     * @param drawable The Drawable to use for the right icon.
     * @return This Alerter
     */
    fun setRightIcon(drawable: Drawable): Alerter {
        alert?.setRightIcon(drawable)

        return this
    }

    /**
     * Set the Alert's Right Icon size
     *
     * @param size Dimension int.
     * @return This Alerter
     */
    fun setRightIconSize(@DimenRes size: Int): Alerter {
        alert?.setRightIconSize(size)

        return this
    }

    /**
     * Set the Alert's Right Icon size
     *
     * @param size Right Icon size in pixel.
     * @return This Alerter
     */
    fun setRightIconPixelSize(@Px size: Int): Alerter {
        alert?.setRightIconPixelSize(size)

        return this
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param color Color int
     * @return This Alerter
     */
    fun setRightIconColorFilter(@ColorInt color: Int): Alerter {
        alert?.setRightIconColorFilter(color)

        return this
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param colorFilter ColorFilter
     * @return This Alerter
     */
    fun setRightIconColorFilter(colorFilter: ColorFilter): Alerter {
        alert?.setRightIconColorFilter(colorFilter)

        return this
    }

    /**
     * Set the right icon color for the Alert
     *
     * @param color Color int
     * @param mode  PorterDuff.Mode
     * @return This Alerter
     */
    fun setRightIconColorFilter(@ColorInt color: Int, mode: PorterDuff.Mode): Alerter {
        alert?.setRightIconColorFilter(color, mode)

        return this
    }

    /**
     * Set the right icons's position for the Alert
     *
     * @param gravity Gravity int
     * @return This Alerter
     */
    fun setRightIconPosition(gravity: Int): Alerter {
        alert?.setRightIconPosition(gravity)

        return this
    }

    /**
     * Set the onClickListener for the Alert
     *
     * @param onClickListener The onClickListener for the Alert
     * @return This Alerter
     */
    fun setOnClickListener(onClickListener: View.OnClickListener): Alerter {
        alert?.setOnClickListener(onClickListener)

        return this
    }

    /**
     * Set the on screen duration of the alert
     *
     * @param milliseconds The duration in milliseconds
     * @return This Alerter
     */
    fun setDuration(milliseconds: Long): Alerter {
        alert?.duration = milliseconds

        return this
    }

    /**
     * Enable or Disable Icon Pulse Animations
     *
     * @param pulse True if the icon should pulse
     * @return This Alerter
     */
    fun enableIconPulse(pulse: Boolean): Alerter {
        alert?.pulseIcon(pulse)

        return this
    }

    /**
     * Set whether to show the icon in the alert or not
     *
     * @param showIcon True to show the icon, false otherwise
     * @return This Alerter
     */
    fun showIcon(showIcon: Boolean): Alerter {
        alert?.showIcon(showIcon)

        return this
    }

    /**
     * Enable or Disable Right Icon Pulse Animations
     *
     * @param pulse True if the right icon should pulse
     * @return This Alerter
     */
    fun enableRightIconPulse(pulse: Boolean): Alerter {
        alert?.pulseRightIcon(pulse)

        return this
    }

    /**
     * Set whether to show the right icon in the alert or not
     *
     * @param showRightIcon True to show the right icon, false otherwise
     * @return This Alerter
     */
    fun showRightIcon(showRightIcon: Boolean): Alerter {
        alert?.showRightIcon(showRightIcon)

        return this
    }

    /**
     * Set whether to show the animation on focus/pressed states
     *
     * @param enabled True to show the animation, false otherwise
     */
    fun enableClickAnimation(enabled: Boolean): Alerter {
        alert?.enableClickAnimation(enabled)

        return this
    }

    /**
     * Enable or disable infinite duration of the alert
     *
     * @param infiniteDuration True if the duration of the alert is infinite
     * @return This Alerter
     */
    fun enableInfiniteDuration(infiniteDuration: Boolean): Alerter {
        alert?.setEnableInfiniteDuration(infiniteDuration)

        return this
    }

    /**
     * Sets the Alert Shown Listener
     *
     * @param listener OnShowAlertListener of Alert
     * @return This Alerter
     */
    fun setOnShowListener(listener: OnShowAlertListener): Alerter {
        alert?.setOnShowListener(listener)

        return this
    }

    /**
     * Sets the Alert Hidden Listener
     *
     * @param listener OnHideAlertListener of Alert
     * @return This Alerter
     */
    fun setOnHideListener(listener: OnHideAlertListener): Alerter {
        alert?.onHideListener = listener

        return this
    }

    /**
     * Enables swipe to dismiss
     *
     * @return This Alerter
     */
    fun enableSwipeToDismiss(): Alerter {
        alert?.enableSwipeToDismiss()

        return this
    }

    /**
     * Enable or Disable Vibration
     *
     * @param enable True to enable, False to disable
     * @return This Alerter
     */
    fun enableVibration(enable: Boolean): Alerter {
        alert?.setVibrationEnabled(enable)

        return this
    }

    /**
     * Set sound Uri
     * if set null, sound will be disabled
     *
     * @param uri To set sound Uri (raw folder)
     * @return This Alerter
     */
    @JvmOverloads
    fun setSound(uri: Uri? = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)): Alerter {
        alert?.setSound(uri)

        return this
    }

    /**
     * Disable touch events outside of the Alert
     *
     * @return This Alerter
     */
    fun disableOutsideTouch(): Alerter {
        alert?.disableOutsideTouch()

        return this
    }

    /**
     * Enable or disable progress bar
     *
     * @param enable True to enable, False to disable
     * @return This Alerter
     */
    fun enableProgress(enable: Boolean): Alerter {
        alert?.setEnableProgress(enable)

        return this
    }

    /**
     * Set the Progress bar color from a color resource
     *
     * @param color The color resource
     * @return This Alerter
     */
    fun setProgressColorRes(@ColorRes color: Int): Alerter {
        alert?.setProgressColorRes(color)

        return this
    }

    /**
     * Set the Progress bar color from a color resource
     *
     * @param color The color resource
     * @return This Alerter
     */
    fun setProgressColorInt(@ColorInt color: Int): Alerter {
        alert?.setProgressColorInt(color)

        return this
    }

    /**
     * Set if the Alert is dismissible or not
     *
     * @param dismissible true if it can be dismissed
     * @return This Alerter
     */
    fun setDismissable(dismissible: Boolean): Alerter {
        alert?.setDismissible(dismissible)

        return this
    }

    /**
     * Set a Custom Enter Animation
     *
     * @param animation The enter animation to play
     * @return This Alerter
     */
    fun setEnterAnimation(@AnimRes animation: Int): Alerter {
        alert?.enterAnimation = AnimationUtils.loadAnimation(alert?.context, animation)

        return this
    }

    /**
     * Set a Custom Exit Animation
     *
     * @param animation The exit animation to play
     * @return This Alerter
     */
    fun setExitAnimation(@AnimRes animation: Int): Alerter {
        alert?.exitAnimation = AnimationUtils.loadAnimation(alert?.context, animation)

        return this
    }

    /**
     * Show a button with the given text, and on click listener
     *
     * @param text The text to display on the button
     * @param onClick The on click listener
     */
    fun addButton(
            text: CharSequence, @StyleRes style: Int = R.style.AlertButton,
            onClick: View.OnClickListener
    ): Alerter {
        alert?.addButton(text, style, onClick)

        return this
    }

    /**
     * Set the Button's Typeface
     *
     * @param typeface Typeface to use
     * @return This Alerter
     */
    fun setButtonTypeface(typeface: Typeface): Alerter {
        alert?.buttonTypeFace = typeface

        return this
    }

    fun getLayoutContainer(): View? {
        return alert?.layoutContainer
    }

    companion object {

        private var decorView: WeakReference<ViewGroup>? = null

        /**
         * Creates the Alert
         *
         * @param activity The calling Activity
         * @return This Alerter
         */
        @JvmStatic
        @JvmOverloads
        fun create(activity: Activity, layoutId: Int = R.layout.alerter_alert_default_layout): Alerter {
            return create(activity = activity, dialog = null, layoutId = layoutId)
        }

        /**
         * Creates the Alert
         *
         * @param dialog The calling Dialog
         * @return This Alerter
         */
        @JvmStatic
        @JvmOverloads
        fun create(dialog: Dialog, layoutId: Int = R.layout.alerter_alert_default_layout): Alerter {
            return create(activity = null, dialog = dialog, layoutId = layoutId)
        }

        /**
         * Creates the Alert with custom view, and maintains a reference to the calling Activity or Dialog's
         * DecorView
         *
         * @param activity The calling Activity
         * @param dialog The calling Dialog
         * @param layoutId Custom view layout res id
         * @return This Alerter
         */
        @JvmStatic
        private fun create(activity: Activity? = null, dialog: Dialog? = null, @LayoutRes layoutId: Int): Alerter {
            val alerter = Alerter()

            //Hide current Alert, if one is active
            clearCurrent(activity, dialog)

            alerter.alert = dialog?.window?.let {
                decorView = WeakReference(it.decorView as ViewGroup)
                Alert(context = it.decorView.context, layoutId = layoutId)
            } ?: run {
                activity?.window?.let {
                    decorView = WeakReference(it.decorView as ViewGroup)
                    Alert(context = it.decorView.context, layoutId = layoutId)
                }
            }

            return alerter
        }

        /**
         * Cleans up the currently showing alert view, if one is present. Either pass
         * the calling Activity, or the calling Dialog
         *
         * @param activity The current Activity
         * @param dialog The current Dialog
         */
        @JvmStatic
        fun clearCurrent(activity: Activity?, dialog: Dialog?) {
            dialog?.let {
                it.window?.decorView as? ViewGroup
            } ?: kotlin.run {
                activity?.window?.decorView as? ViewGroup
            }?.also {
                removeAlertFromParent(it)
            }
        }

        /**
         * Hides the currently showing alert view, if one is present
         */
        @JvmStatic
        fun hide() {
            decorView?.get()?.let {
                removeAlertFromParent(it)
            }
        }

        private fun removeAlertFromParent(decorView: ViewGroup) {
            //Find all Alert Views in Parent layout
            for (i in 0..decorView.childCount) {
                val childView = if (decorView.getChildAt(i) is Alert) decorView.getChildAt(i) as Alert else null
                if (childView != null && childView.windowToken != null) {
                    ViewCompat.animate(childView).alpha(0f).withEndAction(getRemoveViewRunnable(childView))
                }
            }
        }

        /**
         * Check if an Alert is currently showing
         *
         * @return True if an Alert is showing, false otherwise
         */
        @JvmStatic
        val isShowing: Boolean
            get() {
                var isShowing = false

                decorView?.get()?.let {
                    isShowing = it.findViewById<View>(R.id.llAlertBackground) != null
                }

                return isShowing
            }

        private fun getRemoveViewRunnable(childView: Alert?): Runnable {
            return Runnable {
                childView?.let {
                    (childView.parent as? ViewGroup)?.removeView(childView)
                }
            }
        }
    }
}
"""}
