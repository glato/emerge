# Borrowed for testing with real test data from the Deep copy of Pinterest project.
# https://github.com/ivsall2012/AHPinterest

SWIFT_TEST_FILES = {"file1.swift": """
//
//  AHDiscoverContainer.swift
//  AHPinterest
//
//  Created by Andy Hurricane on 4/27/17.
//  Copyright © 2017 AndyHurricane. All rights reserved.
//

import UIKit

class AHDiscoverVC: UICollectionViewController, AHTransitionProperties {
    let navVC = AHDiscoverNavVC()
    let pageLayout = AHPageLayout()
    
    var dictVCs = [Int: AHDiscoverCategoryVC]()
    
    var categoryArr = [String]()
    
    var itemIndex: Int = 0 {
        didSet {
            self.navVC.scrollToItemIndex(index: itemIndex)
        }
    }
    
    weak var selectedCell: AHPinCell?{
        guard itemIndex >= 0 else { return nil }
        
        let pageVC = self.getVC(itemIndex)
        return pageVC.selectedCell
    }
    
    // The current displaying main cell(the large size pin) lives within AHPinContentVC
    weak var presentingCell: AHPinContentCell?{
        guard itemIndex >= 0 else { return nil }
        
        let pageVC = self.getVC(itemIndex)
        return pageVC.presentingCell
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        
        self.automaticallyAdjustsScrollViewInsets = false
        collectionView?.decelerationRate = UIScrollViewDecelerationRateFast
        collectionView?.frame.origin.y = 64 + AHDiscoverNavCellHeight
        collectionView?.contentInset = .init(top: 0, left: 0, bottom: 0, right: 0 )
        setupCollecitonView()

        setupNavVC()
        
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        self.navigationController?.isNavigationBarHidden = false
    }
    
    
    func setupCollecitonView() {
        
        let pageCellNIb = UINib(nibName: AHPageCellID, bundle: nil)
        collectionView?.register(pageCellNIb, forCellWithReuseIdentifier: AHPageCellID)
        
        pageLayout.scrollDirection = .horizontal
        collectionView?.setCollectionViewLayout(pageLayout, animated: false)
    }
    
    func setupNavVC() {
        navVC.delegate = self
        navVC.view.frame = CGRect(x: 0, y: 64, width: self.view.frame.size.width, height: AHDiscoverNavCellHeight)
        
        navVC.willMove(toParentViewController: self)
        self.addChildViewController(navVC)
        navVC.didMove(toParentViewController: self)
        
        
        navVC.view.willMove(toSuperview: self.view)
        self.view.addSubview(navVC.view)
        navVC.view.didMoveToSuperview()
        
        
        AHNetowrkTool.tool.loadCategoryNames { (categoryArr) in
            if let categoryArr = categoryArr, !categoryArr.isEmpty {
                self.categoryArr.append(contentsOf: categoryArr)
                self.navVC.categoryArr = self.categoryArr
                self.collectionView?.reloadData()
            }
        }
    }
    
    func getVC(_ index:Int) -> AHDiscoverCategoryVC {
        guard index < categoryArr.count else {
            fatalError("index out of bound for categoryArr")
        }
        
        if let vc = dictVCs[index] {
            vc.willMove(toParentViewController: self)
            self.addChildViewController(vc)
            vc.didMove(toParentViewController: self)
            return vc
        }else{
            print("created a AHDiscoverCategoryVC")
            let vc = AHDiscoverCategoryVC()
            vc.showLayoutHeader = true
            vc.categoryName = categoryArr[index]
            
            dictVCs[index] = vc
            
            vc.willMove(toParentViewController: self)
            self.addChildViewController(vc)
            vc.didMove(toParentViewController: self)
            
            return vc
        }
        
        
    }


}

extension AHDiscoverVC {
    override func scrollViewDidEndDecelerating(_ scrollView: UIScrollView) {
        let items = collectionView?.visibleCells
        if let items = items, items.count == 1 {
            if let indexPath = collectionView?.indexPath(for: items.first!) {
                self.itemIndex = indexPath.item
            }else{
                fatalError("It has an visible cell without indexPath??")
            }
            
        }else{
            print("visible items have more then 1, problem?!")
        }
    }
}

extension AHDiscoverVC: AHDiscoverNavDelegate {
    func discoverNavDidSelect(at index: Int) {
        guard !categoryArr.isEmpty else {
            return
        }
        self.itemIndex = index
        let indexPath = IndexPath(item: index, section: 0)
        self.collectionView?.scrollToItem(at: indexPath, at: UICollectionViewScrollPosition.right, animated: true)
    }
}

extension AHDiscoverVC: UICollectionViewDelegateFlowLayout {
    func collectionView(_ collectionView: UICollectionView, layout collectionViewLayout: UICollectionViewLayout, sizeForItemAt indexPath: IndexPath) -> CGSize {
        // At first return, collecitonView.bounds.size is 1000.0 x 980.0
        return CGSize(width: screenSize.width, height: screenSize.height)
    }
    
    
}

extension AHDiscoverVC {
    override func collectionView(_ collectionView: UICollectionView, numberOfItemsInSection section: Int) -> Int {
        return categoryArr.count
    }
    

    
    override func collectionView(_ collectionView: UICollectionView, cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        guard !categoryArr.isEmpty else {
            return UICollectionViewCell()
        }
        let cell = collectionView.dequeueReusableCell(withReuseIdentifier: AHPageCellID, for: indexPath) as! AHPageCell
        
        let categoryName = categoryArr[indexPath.item]
        let pageVC = getVC(indexPath.item)
        pageVC.refreshLayout.enableHeaderRefresh = false
        pageVC.sectionTitle = categoryName
        cell.pageVC = pageVC
        return cell
    }
}



// MARK:- Transition Stuff

extension AHDiscoverVC: AHTransitionPushFromDelegate {
    func transitionPushFromSelectedCell() -> AHPinCell? {
        return self.selectedCell
    }
    
}

extension AHDiscoverVC: AHTransitionPushToDelegate {
    
    func transitionPushToPresentingCell() -> AHPinContentCell? {
        return self.presentingCell
    }
    
}

extension AHDiscoverVC: AHTransitionPopFromDelegate {
    func transitionPopToSelectedCell() -> AHPinCell? {
        return self.selectedCell
    }
}

extension AHDiscoverVC: AHTransitionPopToDelegate {
    func transitionPopFromPresentingCell() -> AHPinContentCell? {
        return self.presentingCell
    }
}
""", "file2.swift": """
//
//  AHPopInteractiveHandler.swift
//  AHPinterest
//
//  Created by Andy Hurricane on 4/26/17.
//  Copyright © 2017 AndyHurricane. All rights reserved.
//

import UIKit

class AHPopInteractiveHandler: NSObject {
    weak var pinContentVC: AHPinContentVC! {
        didSet {
            popInteractive.attachView(vc: pinContentVC, view: pinContentVC.view)
        }
    }
    var popInteractive = AHPopInteractive()
    
    
    var presentingCell: AHPinContentCell {
        return pinContentVC.presentingCell!
    }
    
    var selectedCell: AHPinCell {
        return pinContentVC.selectedCell!
    }
    
    var whiteAreaFrame: CGRect {
        return presentingCell.convert(presentingCell.pinImageView.frame, to: pinContentVC.view)
    }
    
    var contentOffSet = CGPoint.zero
    
    override init() {
        super.init()
        popInteractive.delegate = self
    }
}



extension AHPopInteractiveHandler: UICollectionViewDelegate {
    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        contentOffSet = scrollView.contentOffset
    }
}

extension AHPopInteractiveHandler: AHPopInteractiveDelegate {
    func popInteractiveForContentOffset() -> CGPoint {
        return contentOffSet
    }
    func popInteractiveForTriggerYOffset() -> CGFloat {
        guard let inset = pinContentVC?.collectionView?.contentInset else {
            return -9999.0
        }
        return -inset.top
    }
    func popInteractiveForAnimatingSubject() -> UIView{
        let presentingView = presentingCell.pinImageView.snapshotView(afterScreenUpdates: true)
        presentingView!.frame = whiteAreaFrame
        return presentingView!
    }
    
    func popInteractiveForAnimatingSubjectFinalFrame() -> CGRect {
        guard let childViewControllers = pinContentVC.navigationController?.childViewControllers else {
            fatalError("NO childViewControllers?")
        }
        // the last vc the current one, count -1
        // the second last vc is count - 2
        let previousIndex = childViewControllers.count - 2
        
        guard let vc = childViewControllers[previousIndex] as? AHTransitionProperties
            else {
            fatalError("No previous VC comfirming AHTransitionProperties")
        }

        guard let selectedCell = vc.selectedCell else {

            fatalError("No selectedCell")
        }
        
        let previousVC = vc as! UIViewController
        
        let frame = selectedCell.convert(selectedCell.imageView.frame, to: previousVC.view)
        
        return frame
        
    }
    
    func popInteractiveForAnimatingSubjectBackground() -> UIView {
        let bgSnap = pinContentVC.view.snapshotView(afterScreenUpdates: true)
        // give the frame extra 2 points on all sides to cover up fully
        let newFrame = whiteAreaFrame.insetBy(dx: -2, dy: -2)
        let whiteArea = UIView(frame: newFrame)
        whiteArea.backgroundColor = UIColor.white
        bgSnap!.addSubview(whiteArea)
        return bgSnap!
    }
    
    func popInteractiveForAnimatingBackground() -> UIView {
        guard let childViewControllers = pinContentVC.navigationController?.childViewControllers else {
            fatalError("NO childViewControllers?")
        }
        // the last vc the current one, count -1
        // the second last vc is count - 2
        let previousIndex = childViewControllers.count - 2
        
        let finalFrame = self.popInteractiveForAnimatingSubjectFinalFrame()
        let vc = childViewControllers[previousIndex]
        
        let snapshot = vc.view.snapshotView(afterScreenUpdates: true)
        vc.view.layoutIfNeeded()
        
        let newFrame = finalFrame.insetBy(dx: -2, dy: -2)
        let whiteArea = UIView(frame: newFrame)
        whiteArea.backgroundColor = UIColor.white
        snapshot?.addSubview(whiteArea)
        return snapshot!
        
    }
    
}
"""}
